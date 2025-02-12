// Listen for the icon click
chrome.action.onClicked.addListener(function (tab) {
  takeScreenshot(tab);
});

// Listen for keyboard shortcut
chrome.commands.onCommand.addListener(function (command) {
  console.log("Shortcut Command Received:", command); // Debugging log
  if (command === "take_screenshot") {
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      if (tabs.length > 0) {
        takeScreenshot(tabs[0]);
      }
    });
  }
});

function takeScreenshot(tab) {
  let tabUrl = tab.url;

  if (tabUrl) {
    fetch("http://127.0.0.1:5000/capture", {
      method: "POST",
      mode: "cors",  // ✅ Fix CORS for Chrome
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: tabUrl }) 
  })
  
    .then(response => {
      if (!response.ok) {
        throw new Error("Server not available");
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        chrome.notifications.create({
          type: "basic",
          iconUrl: "icons/icon128.png",
          title: "Screenshot",
          message: "Captured successfully"
        }, (notificationId) => {
          setTimeout(() => {
              chrome.notifications.clear(notificationId);
          }, 1000);
      });
      } else {
        console.error("Failed to capture screen.");
      }
    })
    .catch(error => {
      chrome.notifications.create({
        type: "basic",
        iconUrl: "icons/icon128.png",
        title: "Server Error",
        message: "Please turn on the server at http://127.0.0.1:5000"
      }, (notificationId) => {
        setTimeout(() => {
            chrome.notifications.clear(notificationId);
        }, 1000);
    });
      console.error("Fetch error:", error);
    });
  } else {
    console.error("Tab URL is undefined.");
  }
}
