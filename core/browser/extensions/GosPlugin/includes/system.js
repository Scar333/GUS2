let gosuslugiPluginSystem = ( function() {

     const _ID = "gosuslugi.plugin.extension.system";
     let _callbacks = {};

     let _post = function(message,callback){
          _callbacks[message.id] = callback;
          window.postMessage(message, '*');
     };

     let _init = function(){
          window.addEventListener("message", (event) => {
               let message = event.data;
               if(message.node && message.id) {
                    let callback = _callbacks[ message.id ];
                    if (!!callback) {
                         callback(message);
                         delete _callbacks[message.id];
                    }
               }
          }); 
     };

     _init();

     return {

          handshake: function (callback) {
               let message = new GosuslugiPluginMessage(_ID, "system", "handshake", "");
               _post(message, callback);
          },

          echo: function (value, callback) {
               let message = new GosuslugiPluginMessage(_ID, "system", "echo", value);
               _post(message, callback);
          },

          cache: function (value, callback) {
               let message = new GosuslugiPluginMessage(_ID, "system", "cache", value);
               _post(message, callback);
          },

          lastError: function (callback) {
               let message = new GosuslugiPluginMessage(_ID, "system", "lastError", "");
               _post(message, callback);
          },

          config: function (callback) {
               let message = new GosuslugiPluginMessage(_ID, "system", "config", "");
               _post(message, callback);
          },

          ipConfig: function (callback) {
               let message = new GosuslugiPluginMessage(_ID, "system", "ipConfig", "");
               _post(message, callback);
          },

          close: function (callback) {
               let message = new GosuslugiPluginMessage(_ID, "system", "close", "");
               _post(message, callback);
          },

          protocol: function (callback) {
               let message = new GosuslugiPluginMessage(_ID, "system", "protocol", "");
               _post(message, callback);
          },
     };
})();