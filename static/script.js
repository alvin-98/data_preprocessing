class ThemeManager {
  constructor() {
    this.theme = localStorage.getItem("theme") || "light";
    this.initialize();
  }

  initialize() {
    document.documentElement.setAttribute("data-theme", this.theme);
    document.querySelector("html").setAttribute("data-theme", this.theme);
    this.createToggleButton();
  }

  createToggleButton() {
    const button = document.createElement("button");
    button.className = "theme-toggle";
    button.setAttribute("aria-label", "Toggle theme");
    button.innerHTML = this.theme === "light" ? "🌙" : "☀️";
    button.addEventListener("click", () => this.toggleTheme());
    document.body.appendChild(button);
  }

  toggleTheme() {
    this.theme = this.theme === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", this.theme);
    document.querySelector("html").setAttribute("data-theme", this.theme);
    localStorage.setItem("theme", this.theme);
    const button = document.querySelector(".theme-toggle");
    button.innerHTML = this.theme === "light" ? "🌙" : "☀️";
  }
}

class ImageProcessor {
  constructor() {
    this.uploadForm = document.getElementById("uploadForm");
    this.processForm = document.getElementById("processForm");
    this.processSection = document.getElementById("processSection");
    this.imageResults = document.getElementById("imageResults");
    this.originalImage = document.getElementById("originalImage");

    this.initializeEventListeners();
    this.themeManager = new ThemeManager();
  }

  initializeEventListeners() {
    this.uploadForm.addEventListener("submit", (e) => this.handleUpload(e));
    this.processForm.addEventListener("submit", (e) => this.handleProcess(e));
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

      const response = await this.uploadImage(formData);

      if (response.file_path) {
        this.showProcessingOptions(response.file_path);
      }
    } catch (error) {
      this.showError(error.message);
    }
  }

  async handleProcess(e) {
    e.preventDefault();
    try {
      const selectedActions = Array.from(
        document.querySelectorAll('input[name="actions"]:checked')
      ).map((cb) => cb.value);

      if (selectedActions.length === 0) {
        throw new Error("Please select at least one modification");
      }

      const formData = new FormData();
      selectedActions.forEach((action) => formData.append("actions", action));

      const response = await this.processImage(formData);

      if (response.processed_images) {
        this.displayProcessedImages(response.processed_images);
      }
    } catch (error) {
      this.showError(error.message);
    }
  }

  async uploadImage(formData) {
    const response = await fetch("/upload_image/", {
      method: "POST",
      body: formData,
    });
    return await response.json();
  }

  async processImage(formData) {
    const response = await fetch("/process_image/", {
      method: "POST",
      body: formData,
    });
    return await response.json();
  }

  showProcessingOptions(imagePath) {
    this.processSection.classList.remove("hidden");
    this.originalImage.classList.remove("hidden");
    this.originalImage.querySelector("img").src = imagePath;
  }

  displayProcessedImages(images) {
    images.forEach((image) => {
      const div = document.createElement("div");
      div.className = "image-card";
      div.innerHTML = `
                <h3 class="image-title">${this.capitalizeFirst(
                  image.action
                )}</h3>
                <img src="${image.file_path}" alt="${
        image.action
      }" class="image">
                <p class="image-description">${image.description}</p>
            `;
      this.imageResults.appendChild(div);
    });
  }

  showError(message) {
    alert(message); // You could replace this with a better error handling UI
  }

  capitalizeFirst(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }
}

// Initialize the app when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new ImageProcessor();
});
