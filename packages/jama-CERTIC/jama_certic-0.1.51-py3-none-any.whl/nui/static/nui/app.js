up.link.config.followSelectors.push('a[href]');
up.link.config.preloadSelectors.push('a[href]');
up.form.config.submitSelectors.push(['form']);
up.history.config.restoreTargets = ["main"];
up.fragment.config.runScripts = false;
//up.fragment.config.navigateOptions.transition = 'cross-fade'

up.compiler('.popimage', function (element) {
  new bootstrap.Popover(element, {
    html: true,
    trigger: 'hover',
    content: function () {
      return `
        <div class="popimagecontainer">
          <img class="popimageimage" src="${element.dataset.imgsrc}" />
        </div>`;
    }
  })
});

up.compiler(".openseadragon", function (element) {
  OpenSeadragon({
    element: element,
    prefixUrl: "/static/nui/openseadragon-bin-5.0.1/images/",
    tileSources: element.dataset.manifest
  });
});

up.compiler(".check_all_items", function (element) {
  element.addEventListener("click", function () {
    check_boxes = document.getElementsByClassName("item_check");
    for (let i = 0; i < check_boxes.length; i++) {
      console.log(element.checked);
      check_boxes[i].checked = element.checked;
    }
  });
});

up.compiler("input.dashrow", function(el){
  el.addEventListener("click", function(){
    let closest_tr = el.closest("tr");
    if(el.checked){
      closest_tr.classList.add("opacity-25");
      closest_tr.classList.add("removeRow");
    }else{
      closest_tr.classList.remove("opacity-25");
      closest_tr.classList.remove("removeRow");
    }
  });
});


function removeRow(event){
  event.preventDefault();
  event.target.closest("tr").remove();
}

up.compiler("textarea.stripvalue", function(el){
  el.addEventListener("change", function(){
    el.value = el.value.trim();
  });
});

up.compiler("button.newMetaval", function(el){
  el.addEventListener("click", function(evt){
    evt.preventDefault();
    let clon = document.getElementById("newMetaval").content.cloneNode(true);
    let target = document.querySelector("#itemProperties tbody tr:last-child")
    target.insertAdjacentElement('beforebegin',clon.firstElementChild);
  });
});

function setMetaIdForRow(event){
  event.target.closest("tr").querySelector("textarea").setAttribute("name", "addvalue_" + event.target.value);
}

;(function () {
  const htmlElement = document.querySelector("html");
  if (htmlElement.getAttribute("data-bs-theme") === 'auto') {
      function updateTheme() {
        console.log(window.matchMedia("(prefers-color-scheme: dark)").matches);
          document.querySelector("html").setAttribute("data-bs-theme",
              window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      }
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateTheme)
      updateTheme();
  }
})();