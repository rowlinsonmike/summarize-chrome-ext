// Decode  unicode in summarized string returned from api
function decodeUnicode(str) {
  return str?.replace(/\\u[\dA-F]{4}/gi, function (match) {
    return String.fromCharCode(parseInt(match.replace(/\\u/g, ""), 16));
  });
}

function renderParagraphs(element, inputString) {
  // split string into paragraphs
  const paragraphs = inputString.split("\n\n");
  // make each string in list a <p> element
  const htmlParagraphs = paragraphs.map((para) => `<p>${para}</p>`);
  // join elements together
  const htmlContent = htmlParagraphs.join("");
  // inject into html
  element.innerHTML = htmlContent;
}

//load existing content when the extension is opened
chrome.storage.local.get(["state"], (result) => {
  const element = document.getElementById("summary_content");
  renderParagraphs(element, decodeUnicode(result?.state || ""));
});

//listen for message from serviceworker that state has been updated
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.name === "update") {
    chrome.storage.local.get(["state"], (result) => {
      const element = document.getElementById("summary_content");
      renderParagraphs(element, decodeUnicode(result?.state || ""));
    });
  }
});

//listen for button to be clicked to make call to api
const myButton = document.querySelector("#btn-prompt");
myButton.addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({
    active: true,
    currentWindow: true,
  });
  chrome.runtime.sendMessage({ name: "sendpopup", tab });
});
