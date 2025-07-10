### 🔧 What the architecture currently looks like (simplified):

```
[Frontend View]
     ↓ uses
[ApiCallMixin]
     ↓ calls
[ApiRequest] ← holds → [ApiClient]
```

* `ApiClient`: Manages the network layer (based on `QNetworkAccessManager`).
* `ApiRequest`: Wraps a single API call, connects to the response/error, and emits its own `finished` signal.
* `ApiCallMixin`: Added to each frontend widget to simplify making calls (stores request list, routes callbacks).
* Frontend View: Calls `self.call_api(...)` via the mixin.
