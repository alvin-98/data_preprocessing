import { ThemeManager } from "./utils/ThemeManager.js";
import { UIHelper } from "./utils/UIHelper.js";
import { ImageProcessor } from "./processors/ImageProcessor.js";
import { TextProcessor } from "./processors/TextProcessor.js";
import { AudioProcessor } from "./processors/AudioProcessor.js";

class DataProcessor {
  constructor() {
    this.currentDataType = null;
    this.themeManager = new ThemeManager();
    this.processors = {
      image: new ImageProcessor(),
      text: new TextProcessor(),
      audio: new AudioProcessor(),
    };
    this.initializeEventListeners();
  }

  initializeEventListeners() {
    // Data type selection
    document.querySelectorAll(".btn-type").forEach((button) => {
      button.addEventListener("click", () =>
        this.handleDataTypeSelection(button)
      );
    });

    // Form submissions
    const forms = {
      upload: document.getElementById("uploadForm"),
      image: document.getElementById("imageProcessForm"),
      text: document.getElementById("textProcessForm"),
      audio: document.getElementById("audioProcessForm"),
    };

    forms.upload.addEventListener("submit", (e) => this.handleUpload(e));
    Object.entries(forms).forEach(([type, form]) => {
      if (type !== "upload") {
        form.addEventListener("submit", (e) => this.handleProcess(e));
      }
    });
  }

  handleDataTypeSelection(button) {
    // Remove previous selection
    document.querySelectorAll(".btn-type").forEach((btn) => {
      btn.classList.remove("selected");
    });

    // Update current selection
    button.classList.add("selected");
    this.currentDataType = button.dataset.type;

    // Show upload section
    UIHelper.showElement(document.getElementById("uploadSection"));

    // Update file input accept attribute
    this.updateFileInputAccept();

    // Hide all process sections and results
    this.hideAllSections();
  }

  updateFileInputAccept() {
    const fileInput = document.getElementById("file");
    const acceptTypes = {
      image: "image/*",
      text: ".txt,.doc,.docx",
      audio: "audio/*,.wav,.mp3,.ogg",
    };
    fileInput.accept = acceptTypes[this.currentDataType] || "";
  }

  hideAllSections() {
    const sections = [
      "imageProcessSection",
      "textProcessSection",
      "audioProcessSection",
      "resultsSection",
      "originalContent",
    ];
    sections.forEach((section) =>
      UIHelper.hideElement(document.getElementById(section))
    );
    document.getElementById("processedContent").innerHTML = "";
  }

  async handleUpload(e) {
    e.preventDefault();
    try {
      const formData = new FormData();
      const fileInput = document.getElementById("file");

      if (!fileInput.files[0]) {
        throw new Error("Please select a file");
      }

      formData.append("file", fileInput.files[0]);
      formData.append("type", this.currentDataType);

      const response = await this.uploadFile(formData);
      await this.showProcessingOptions(response.file_path);
    } catch (error) {
      UIHelper.showError(`Upload failed: ${error.message}`);
    }
  }

  async uploadFile(formData) {
    const response = await fetch("/upload/", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    if (!data.file_path) {
      throw new Error("No file path received from server");
    }

    return data;
  }

  async showProcessingOptions(filePath) {
    // Hide all process sections
    this.hideAllSections();

    // Show appropriate process section
    const processSection = `${this.currentDataType}ProcessSection`;
    UIHelper.showElement(document.getElementById(processSection));

    // Show results section and original content
    UIHelper.showElement(document.getElementById("resultsSection"));
    const originalContent = document.getElementById("originalContent");
    UIHelper.showElement(originalContent);

    const contentDisplay = originalContent.querySelector(".content-display");
    const processor = this.processors[this.currentDataType];
    await processor.displayContent(contentDisplay, filePath);
  }

  async handleProcess(e) {
    e.preventDefault();
    try {
      const formData = await this.prepareProcessFormData();
      const response = await this.processContent(formData);
      await this.displayResults(response);
    } catch (error) {
      UIHelper.showError(`Processing failed: ${error.message}`);
    }
  }

  async prepareProcessFormData() {
    const selectedActions = Array.from(
      document.querySelectorAll(
        `#${this.currentDataType}ProcessForm input[name="actions"]:checked`
      )
    ).map((cb) => cb.value);

    if (selectedActions.length === 0) {
      throw new Error("Please select at least one modification");
    }

    const contentDisplay = document
      .getElementById("originalContent")
      .querySelector(".content-display");

    const processor = this.processors[this.currentDataType];
    const filePath = processor.getFilePath(contentDisplay);

    if (!filePath) {
      throw new Error("No file path found");
    }

    const formData = new FormData();
    formData.append("file_path", filePath);
    selectedActions.forEach((action) => formData.append("actions", action));
    formData.append("type", this.currentDataType);

    return formData;
  }

  async processContent(formData) {
    const response = await fetch("/process/", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.error || `HTTP error! status: ${response.status}`
      );
    }

    const data = await response.json();
    if (data.error) {
      throw new Error(data.error);
    }

    if (!data.processed_images?.length) {
      throw new Error("No processed content received from server");
    }

    return data;
  }

  async displayResults(data) {
    const container = document.getElementById("processedContent");
    UIHelper.clearContent(container);

    const processor = this.processors[this.currentDataType];
    data.processed_images.forEach((result) => {
      const div = document.createElement("div");
      div.className = "content-card";
      processor.displayProcessedContent(div, result);
      container.appendChild(div);
    });
  }
}

// Initialize the app when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new DataProcessor();
});
