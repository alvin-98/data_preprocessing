export class UIHelper {
  static showError(message) {
    console.error(message);
    alert(message);
  }

  static capitalizeFirst(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }

  static clearContent(element) {
    element.innerHTML = "";
  }

  static hideElement(element) {
    element.classList.add("hidden");
  }

  static showElement(element) {
    element.classList.remove("hidden");
  }
}
