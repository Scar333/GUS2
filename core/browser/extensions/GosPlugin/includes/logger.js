let logger = (function() {

     const _ID = "gosuslugi.plugin.extension.logger";

     const _CAPACITY = 1000;

     let _records = JSON.parse(localStorage.getItem(_ID)) || [];
     let _debug = true;

     function _timestamp() {
          let date = new Date();
          return ("0"+(date.getDate()     )).slice(-2) + "." +
                 ("0"+(date.getMonth() + 1)).slice(-2) + "." +
                 (    (date.getFullYear() ))           + " " + 
                 ("0"+(date.getHours()    )).slice(-2) + ":" +
                 ("0"+(date.getMinutes()  )).slice(-2) + ":" +
                 ("0"+(date.getSeconds()  )).slice(-2);
     };

     function _format(node, message) {

          return [_timestamp(), _ID, node, message].join(" ");
     };

     function _save() {
          if (_records) {
               _records.splice(0, _records.length - _CAPACITY);
               localStorage.setItem(_ID , JSON.stringify(_records));
          }
     };

     return {
          info: function(node, message) {
               return (_debug) ? console.info(_format(node, message)) : undefined;
          },

          error: function(node, message) {
               console.error(_format(node, message));
          },

          save: function(node, message) {
               _records.push(_format(node, message));
               _save();
          },

          debug: function(state) {
            _debug = state;
          },

          reset: function() {
               _records = [];
               localStorage.clear();
         }
     };
})();

