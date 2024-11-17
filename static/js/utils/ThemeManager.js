export class ThemeManager {
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
