# *TODOs KANBAN*

## Priority

TODO: Collections must show results:
    - Scroll to last item is not working

TODO: Study how to show Modbus results at request header, not only in general information to improve/ensure/show the user the request has been done. Insert qframe with summary data. Remove "general information" qbox on modbus results tab.

TODO: STUDY - continuous requests in a request type, like a background process or a number of consecutive calls

## Future HIGH PRIORITY

TODO: change self.item.last_response by self.item.last_result for better legibility

TODO: model and components must be in backend layer (decouple frontend and backend). Frontend calls backend manager which returns JSON with data or saves/updates.

TODO: move pickle to SQLITE. Also, save results history per request and collection.

TODO: show history in requests

TODO: collections must have table view option and show history

TODO: Protect SQLite by encrypting 

TODO: Understand read discrete input modbus response

## Future LOW PRIORITY

TODO: BATCH execution 

TODO: Test without automatically reconnecting client

TODO: Data types convert with LSB or MSB - compare with modscan

TODO: documentation

TODO: Pre-request conditions as time sleep

TODO: Splitter must be a component with stretch factor: not expand on first element and expand on second, always.

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

TODO: add_widget method of custmo qgridlayout must save by key, so accessing its elements can be easier and more clear than an index.
