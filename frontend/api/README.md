## 📄 PyQt API Architecture with Safe Lifecycle Management

### 🔧 What the architecture currently looks like (simplified):

```
[Frontend View]
     ↓ uses
[ApiCallMixin]
     ↓ creates
[ApiRequest] ← holds → [ApiClient]
```

---

### 🧩 Component Responsibilities

* **`ApiClient`**

  * Manages low-level HTTP interactions using `QNetworkAccessManager`.
  * Emits success/failure responses using optional `callback` or through custom signals.
  * Logs detailed request/response info and handles HTTP errors.

* **`ApiRequest`**

  * Represents a single API call.
  * Emits `finished` and `error` signals when the response arrives.
  * Decouples backend interaction from frontend view logic.
  * Optionally integrates `weakref` safety via view-level logic.

* **`ApiCallMixin`**

  * Reusable Mixin added to any `QWidget` or `QDialog`.
  * Provides `call_api()` method to initiate and safely manage API requests.
  * Stores requests to prevent garbage collection.
  * Uses `weakref` to ensure callbacks don’t run on deleted views.

* **Frontend View (e.g. `MyDialog`)**

  * Calls `self.call_api(...)` to make requests.
  * Defines response/error handlers.
  * Cleans up requests automatically on close.

---

### 🔁 Typical Workflow

1. A view (e.g. a dialog or widget) inherits from `ApiCallMixin`.
2. The view calls `self.call_api(method, endpoint, callback, ...)`.
3. The mixin creates an `ApiRequest`, connects signals to **safe callbacks** (guarded by `weakref`).
4. The request is stored in `self._api_requests` to prevent it from being garbage collected too early.
5. When the request completes, the result is passed only if the view is still alive.
6. On `closeEvent`, the view clears `self._api_requests` to stop any remaining network activity.

---

### 🧠 Why `weakref` is important

Without it:

* If a view is destroyed (e.g. user navigates away) **before** the API reply arrives,
* The callback might run on a **deleted Python object**,
* Resulting in crashes like:

  ```
  RuntimeError: wrapped C/C++ object of type MyDialog has been deleted
  ```

With `weakref.ref(self)`:

* Each callback checks if the view still exists before calling:

  ```python
  def safe_callback(data):
      view = self._self_weak()
      if view:
          view.handle_success(data)
  ```

> ✅ This guarantees that callbacks only run on live views, preventing silent bugs or runtime crashes.

---

### 🧼 Garbage Collection (GC) and `self._api_requests`

* `ApiRequest` is a `QObject` — if no Python variable keeps a reference, it may be **garbage collected** before the request finishes.
* By appending it to `self._api_requests`, we **retain the object** until the view is done.
* On `closeEvent`, we call:

  ```python
  self._api_requests.clear()
  ```

  to:

  * Release memory,
  * Allow GC to clean up `ApiRequest`,
  * And cancel any remaining signals/connections.

---

### ✅ Summary of Safety Measures

| Mechanism                                    | Purpose                                                    |
| -------------------------------------------- | ---------------------------------------------------------- |
| `self._api_requests.append(...)`             | Prevent premature GC of active requests                    |
| `self._api_requests.clear()` in `closeEvent` | Cancel all pending API activity when the view is destroyed |
| `weakref.ref(self)` in callback wrappers     | Avoid crashes by skipping callbacks to deleted views       |
