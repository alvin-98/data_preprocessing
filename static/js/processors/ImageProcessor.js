import { UIHelper } from "../utils/UIHelper.js";

export class ImageProcessor {
  displayContent(contentDisplay, filePath) {
    contentDisplay.innerHTML = `<img src="${filePath}" alt="Original" class="image" data-path="${filePath}">`;
  }

  displayProcessedContent(div, result) {
    div.innerHTML = `
            <h3 class="content-title">${UIHelper.capitalizeFirst(
              result.action
            )}</h3>
            <img src="${result.file_path}" alt="${result.action}" class="image">
            <p class="content-description">${result.description}</p>
        `;
  }

  getFilePath(contentDisplay) {
    return contentDisplay.querySelector("img").dataset.path;
  }
}
