# *TODOs KANBAN*

## Priority

TODO: Collections must show results:
    - Tree view must be expanded in window and data
    - Update tree view in real time
    - Show timestamp
    - Show elapsed time

TODO: Study how to show Modbus results at request header, not only in general information to improve/ensure/show the user the request has been done

TODO: STUDY - continuous requests in a request type, like a background process or a number of consecutive calls

## Future

TODO: collections tree view must preload all requests and show in real time: "waiting", "in progress", "done"

TODO: change self.item.last_response by self.item.last_result for better legibility

TODO: model and components must be in backend layer (decouple frontend and backend). Frontend calls backend manager which returns JSON with data or saves/updates.

TODO: Test without automatically reconnecting client

TODO: Data types convert with LSB or MSB - compare with modscan

TODO: documentation

TODO: Pre-request conditions as time sleep

TODO: QGridLayout custom component must read table items by key str, not list. It must be a dictionary for better identification

TODO: process raw data to extract registers from write multiple registers

TODO: disable edit items on response table

TODO: export button is broken

TODO: execute button maintains like clicked. Avoid to be clicked until request has reached

TODO: results table. Think about how to adjunts results table to show all return text

TODO: add description tab to all requests

TODO: think about moving general results tab to top view. Or add vertical splitter to show all information directly

TODO: improve usability: save last tab opened in each request

TODO: Print all results in different format types

TODO: add connection name for reusability

TODO: allow to reuse "previous" connections

TODO: allow to export results

TODO: MQTT

TODO: Modbus TLS/Socket/ASCII
