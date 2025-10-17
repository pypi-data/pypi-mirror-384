//Handling Viewports
const handleViewport = () => {
  let viewportWidth = window.innerWidth > 1024 ? window.innerWidth : 1024;
  if (window.location.pathname !== "/login") {
    document
      .querySelector('meta[name="viewport"]')
      .setAttribute("content", `width=${viewportWidth}, initial-scale=1`);
  }
};

window.addEventListener("resize", handleViewport);
handleViewport();
