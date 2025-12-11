let content = (function () {
     const _ID = "gosuslugi.plugin.extension.content";
     let _cache = {};

     let _registered = function (id) {
          let result = false;
          let contentAttribute = document.head.querySelector('meta[content=extension]');
          if (contentAttribute) {
               if (id) {
                    let propertyAttribute = contentAttribute.getAttribute('property');
                    result = !!propertyAttribute && ( propertyAttribute == _ID );
               }
          }
          return result;
     };
     
     let _init = function () {
          document.addEventListener("DOMContentLoaded", function () {
               if(_registered()){
                  console.warn(_ID + " web page allready registered extension, injection of current extension skipped");
                  let message = new GosuslugiPluginMessage(_ID, "system", "disconnect", "");
                  chrome.runtime.sendMessage(message);
                  return;
               }
          
               let meta = document.createElement('meta');
               meta.setAttribute('content', 'extension');
               meta.setAttribute('property', _ID);

               let elements = document.getElementsByTagName('head');
               if (elements.length) {
                    elements[0].appendChild(meta);
                    console.info(_ID + " registered in web page");
               }

               window.addEventListener("message", (event) => {
                    let message = event?.data;
                    let meta = message?.meta;

                    if (meta?.format?.category === "gosuslugi.plugin") {

                         if (message?.node === "") {
                              const id = message.id;
                              const routeNode = meta.routes?.[0]?.node;

                              if (message.mode == "debug") console.info(_ID + " get from web page message: " + JSON.stringify(message));
                              else                         console.info(_ID + " get from web page message id: " + id);

                              _cache[id] = routeNode;

                                console.info(_ID + " send to background message id: " + id);

                                chrome.runtime.sendMessage(message);
                                message = null;
                         }
                    }
               });

               chrome.runtime.onMessage.addListener(
                    function (message, sender, sendResponse) {
                         if (!sender.tab) {
                             let id = message.id;

                              if (message.mode == "debug") console.info(_ID + " get from background message: " + JSON.stringify(message));
                              else                         console.info(_ID + " get from background message id: " + message.id);

                              let cached = _cache[id];
                              if (cached) {
                                   message.meta.routes.push(new GosuslugiPluginRoute(_ID, new Date().toLocaleString()));
                                   message.node = cached;
                                   delete _cache[id];

                                   console.info(_ID + " send to web page message id: " + message.id);

                                   window.postMessage(message, '*');
                              }
                         }
                         sendResponse(null);
                    });
          });
     };

     _init();

     return {
          registered: function () {
               return _registered(ID);
          }
     };
})();