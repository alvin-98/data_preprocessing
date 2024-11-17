import { UIHelper } from "../utils/UIHelper.js";

export class TextProcessor {
  async displayContent(contentDisplay, filePath) {
    contentDisplay.dataset.path = filePath;
    await this.fetchAndDisplayText(filePath, contentDisplay);
  }

  async fetchAndDisplayText(filePath, element) {
    try {
      const response = await fetch(`/view_content/?path=${filePath}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.content) {
        element.textContent = data.content;
      } else {
        throw new Error("No content received from server");
      }
    } catch (error) {
      UIHelper.showError(`Error loading text content: ${error.message}`);
    }
  }

  displayProcessedContent(div, result) {
    const changesList = result.changes
      .map(
        (change) =>
          `<li><span class="original">${
            change[0]
          }</span> → <span class="modified">${
            change[1] || "(removed)"
          }</span></li>`
      )
      .join("");

    const wordCountDiff = result.word_count.after - result.word_count.before;
    const wordCountText =
      wordCountDiff === 0
        ? "No change in word count"
        : `Word count ${
            wordCountDiff > 0 ? "increased" : "decreased"
          } by ${Math.abs(wordCountDiff)}`;

    div.innerHTML = `
            <h3 class="content-title">${UIHelper.capitalizeFirst(
              result.action
            )}</h3>
            <div class="content-stats">
                <p class="word-count">${wordCountText}</p>
                ${
                  result.changes.length > 0
                    ? `
                    <div class="changes-list">
                        <h4>Example Changes:</h4>
                        <ul>${changesList}</ul>
                    </div>
                `
                    : ""
                }
            </div>
            <div class="content-display">${result.content}</div>
            <p class="content-description">${result.description}</p>
        `;
  }

  getFilePath(contentDisplay) {
    return contentDisplay.dataset.path;
  }
}
