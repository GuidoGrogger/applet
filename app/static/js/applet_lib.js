function updateApplet(uuid, iframe) {
    let lastModified = { storage: null, html: null };

    // Helper function to create the proxy script
    function createProxyScript(storageData) {
      return `
        (function() {
          var localStorageData = ${JSON.stringify(storageData)};
          function createLocalStorageWrapper(onStorageChanged) {
            return {
              setItem(key, value) {
                if (typeof key !== 'string') {
                  throw new TypeError("Keys must be strings");
                }
                localStorageData[key] = value.toString();
                onStorageChanged(localStorageData);
              },
              getItem(key) {
                return localStorageData[key] || null;
              },
              removeItem(key) {
                delete localStorageData[key];
                onStorageChanged(localStorageData);
              },
              clear() {
                localStorageData = {};
                onStorageChanged(localStorageData);
              },
              key(index) {
                return Object.keys(localStorageData)[index] || null;
              },
              get length() {
                return Object.keys(localStorageData).length;
              }
            };
          }
          var onStorageChanged = function(updatedData) {
            window.parent.postMessage({ type: 'storageChanged', data: updatedData }, '*');
          };
          Object.defineProperty(window, 'localStorage', {
            value: createLocalStorageWrapper(onStorageChanged),
            writable: false,
            configurable: false,
            enumerable: true
          });
        })();
      `;
    }
  
    // Helper function to load the applet into the iframe
    function loadApplet(storageData, htmlContent) {
      // Ensure storageData is an object, initialize as empty if not
      if (typeof storageData !== 'object' || storageData === null || Array.isArray(storageData)) {
        storageData = {};
      }
    
      const proxyScript = createProxyScript(storageData);
      const modifiedHtmlContent = htmlContent.replace('<head>', `<head><script>${proxyScript}</script>`);

      // Save the scroll position
      const scrollPosition = {
        x: iframe.contentWindow?.scrollX || 0,
        y: iframe.contentWindow?.scrollY || 0
      };

      // Set the iframe's srcdoc to the modified HTML content
      iframe.srcdoc = modifiedHtmlContent;

      // Restore the scroll position after the iframe loads
      iframe.onload = function() {
        iframe.contentWindow.scrollTo(scrollPosition.x, scrollPosition.y);
      };
    }
  
    // Function to fetch storage data and HTML content
    function fetchAppletData() {
      return Promise.all([
        fetch(`/applet/${uuid}/storage`, { cache: 'no-cache' }),
        fetch(`/applet/${uuid}/html`, { cache: 'no-cache' })
      ]);
    }
  
    // Initial load of the applet
    function initialLoad() {
      fetchAppletData()
        .then(async ([storageResponse, htmlResponse]) => {
          if (!storageResponse.ok || !htmlResponse.ok) {
            throw new Error('Failed to fetch storage or HTML content');
          }

          lastModified.storage = storageResponse.headers.get('Last-Modified');
          lastModified.html = htmlResponse.headers.get('Last-Modified');
          const storageData = await storageResponse.json();
          const htmlContent = await htmlResponse.text();

          loadApplet(storageData, htmlContent);
        })
        .catch(err => {
          console.error('Error during initial load:', err);
        });
    }
  
    // Function to reload the applet when updates are detected
    function reloadApplet() {
      fetchAppletData()
        .then(async ([storageResponse, htmlResponse]) => {
          if (!storageResponse.ok || !htmlResponse.ok) {
            throw new Error('Failed to fetch storage or HTML content');
          }

          lastModified.storage = storageResponse.headers.get('Last-Modified');
          lastModified.html = htmlResponse.headers.get('Last-Modified');
          const storageData = await storageResponse.json();
          const htmlContent = await htmlResponse.text();

          loadApplet(storageData, htmlContent);
        })
        .catch(err => {
          console.error('Error during reload:', err);
        });
    }
  
    // Periodically check for updates from the server
    function checkForUpdates() {
      Promise.all([
        fetch(`/applet/${uuid}/storage`, { method: 'HEAD', cache: 'no-cache' }),
        fetch(`/applet/${uuid}/html`, { method: 'HEAD', cache: 'no-cache' })
      ])
        .then(([storageResponse, htmlResponse]) => {
          if (storageResponse.ok && htmlResponse.ok) {
            const serverStorageLastModified = storageResponse.headers.get('Last-Modified');
            const serverHtmlLastModified = htmlResponse.headers.get('Last-Modified');
            
            if ((serverStorageLastModified && serverStorageLastModified !== lastModified.storage) ||
                (serverHtmlLastModified && serverHtmlLastModified !== lastModified.html)) {
              console.log('New version found. Reloading applet...');
              lastModified.storage = serverStorageLastModified;
              lastModified.html = serverHtmlLastModified;
              reloadApplet();
            }
          }
        })
        .catch(err => {
          console.error('Error checking for updates:', err);
        });
    }
  
    // Listen for storage changes from the iframe
    window.addEventListener('message', event => {
      if (event.data?.type === 'storageChanged') {
        const updatedData = event.data.data;
  
        // Send PUT request to update storage data on server
        fetch(`/applet/${uuid}/storage`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(updatedData)
        })
          .then(response => {
            if (response.ok) {
              console.log('Storage data updated on server');
              console.log('Updated storage data:', JSON.stringify(updatedData)); // Log the updated storage data
            } else {
              throw new Error('Failed to update storage data');
            }
          })
          .catch(err => {
            console.error('Error updating storage data:', err);
          });
      }
    });
  
    // Start the periodic update check
    setInterval(checkForUpdates, 333);
  
    // Perform the initial load
    initialLoad();
  }
  
  async function handleCleanData(selectedApplet) {
    if (selectedApplet) {
        try {
            const response = await fetch(`/applet/${selectedApplet}/storage`, {
                method: 'DELETE',
            });
            if (response.ok) {
                console.log('Storage data deleted on server');
            } else {
                throw new Error('Failed to clean applet data.');
            }
        } catch (error) {
            console.error('Error cleaning applet data:', error);
        }
    }
}

async function changeApplet(uuid, audioBlob) {
  const formData = new FormData();
  formData.append('audio', audioBlob);

  try {
    const response = await fetch(`/applet/${uuid}`, {
      method: 'POST',
      body: formData
    });

    if (response.ok) {
      const data = await response.json();
      return data.uuid;
    } else {
      throw new Error('Failed to change applet');
    }
  } catch (error) {
    console.error('Error changing applet:', error);
    throw error;
  }
}
