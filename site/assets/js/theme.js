const themePreference = window.matchMedia("(prefers-color-scheme: dark)");
const themeRoot = document.documentElement;
const themeStorageKey = "thetomtimes-theme";

try {
  const storedTheme = localStorage.getItem(themeStorageKey);
  if (storedTheme === "light" || storedTheme === "dark") {
    themeRoot.dataset.theme = storedTheme;
  }
} catch {
  // The system preference still works when storage is unavailable.
}

document.addEventListener("DOMContentLoaded", () => {
  const button = document.querySelector(".theme-toggle");
  const currentTheme = () => themeRoot.dataset.theme || (themePreference.matches ? "dark" : "light");

  function updateButton() {
    button.setAttribute("aria-label", currentTheme() === "dark" ? "Attiva il tema chiaro" : "Attiva il tema scuro");
  }

  button.addEventListener("click", () => {
    const nextTheme = currentTheme() === "dark" ? "light" : "dark";
    themeRoot.dataset.theme = nextTheme;
    updateButton();
    try {
      localStorage.setItem(themeStorageKey, nextTheme);
    } catch {
      // Keep the selected theme for this page.
    }
  });

  themePreference.addEventListener("change", updateButton);
  updateButton();
  button.hidden = false;
});
