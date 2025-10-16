document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("pre button.md-clipboard").forEach(button => {
    button.setAttribute("title", "Copy code"); // custom tooltip
    button.addEventListener("click", () => {
      button.setAttribute("title", "Copied!");
      setTimeout(() => button.setAttribute("title", "Copy code"), 1500);
    });
  });
});
