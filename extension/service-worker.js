chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.name === "sendpopup") {
    fetch("<FUNCTION URL>", {
      method: "POST",
      headers: {
        Authorization: "Bearer <TOKEN>",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: message.tab.url }),
    })
      .then((response) => response.json())
      .then((data) => {
        chrome.storage.local.set({
          state:
            data?.result !== "" ? data?.result : "Unable to summarize site",
        });
        chrome.runtime.sendMessage({ name: "update" });
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  }
});
