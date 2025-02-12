// Listen for icon click
browser.browserAction.onClicked.addListener(() => {
    captureScreenshot();
});

// Listen for keyboard shortcut
browser.commands.onCommand.addListener((command) => {
    if (command === "run-foo") {
        captureScreenshot();
    }
});

// Capture Screenshot with Current Tab URL
function captureScreenshot() {
    browser.tabs.query({ active: true, currentWindow: true }).then((tabs) => {
        if (tabs.length === 0) {
            console.error("No active tab found.");
            return;
        }

        let currentTab = tabs[0];
        let tabUrl = currentTab.url; // Get the current tab's URL

        browser.tabs.captureVisibleTab().then((image) => {
            sendToServer(image, tabUrl); // Send image + URL
        }).catch((error) => {
            console.error("Screenshot capture failed:", error);
        });
    });
}


// Convert Base64 to Blob
function base64ToBlob(base64) {
    let byteCharacters = atob(base64.split(',')[1]); // Remove 'data:image/png;base64,' part
    let byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    let byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: "image/png" });
}

// Sanitize URL for Filename
function sanitizeUrl(url) {
    try {
        let parsedUrl = new URL(url);
        let domain = parsedUrl.hostname.replace(/^www\./, ""); // Remove 'www.'
        let path = parsedUrl.pathname.replace(/\//g, "_").replace(/[^a-zA-Z0-9._-]/g, ""); // Replace / with _
        return `${domain}${path ? "_" + path : ""}`; // Example: "example_com_page"
    } catch (error) {
        console.error("Invalid URL:", url);
        return "screenshot"; // Fallback name
    }
}

// Send Screenshot to Server as a Blob with URL-based Filename
function sendToServer(image, url) {
    let blob = base64ToBlob(image);
    let sanitizedFilename = sanitizeUrl(url) + ".png"; // Generate filename from URL

    let formData = new FormData();
    formData.append("file", blob, sanitizedFilename); // Send with proper name
    formData.append("url", url); // Send URL to the server

    fetch("http://127.0.0.1:5000/capture", {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Server not available");
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            browser.notifications.create({
                type: "basic",
                iconUrl: "icon128.png",
                title: "Screenshot",
                message: "Captured successfully"
            }).then(notificationId => {
                setTimeout(() => {
                    browser.notifications.clear(notificationId);
                }, 1000);
            });
        } else {
            console.error("Failed to send screenshot.");
        }
    })
    .catch(error => {
        browser.notifications.create({
            type: "basic",
            iconUrl: "icon128.png",
            title: "Server Error",
            message: "Please turn on the server at http://127.0.0.1:5000"
        }).then(notificationId => {
            setTimeout(() => {
                browser.notifications.clear(notificationId);
            }, 1000);
        });
        console.error("Fetch error:", error);
    });
}
