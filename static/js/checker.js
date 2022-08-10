function checkParentBox(box) {
   if(box instanceof HTMLInputElement) {
     box.checked = true   
   }
   const parentOfThisBox = box.closest('.nested');
   if(parentOfThisBox) {
     const parLi = parentOfThisBox.parentNode;
     checkParentBox(parLi.children[0])
   }
}

function uncheckChildBox(box) {
  for(var c = 0; c < box.children.length; c++) {
    if(box.children[c].className=="option" || box.children[c].className=="subOption") {
      box.children[c].checked = false;
    }
    if(box.children[c].children.length > 0) {
      uncheckChildBox(box.children[c]);
    }
  }    
}

var checkboxes = document.querySelectorAll('input.subOption');
for(var i = 0; i < checkboxes.length; i++) {
  checkboxes[i].onclick = function() {
    const parentWithClass = this.closest('.nested');
    if(parentWithClass && this.checked) {
      const parentLi = parentWithClass.parentNode;
        if(parentLi && parentLi.children[0]) {
          checkParentBox(parentLi.children[0]);
        }
     }
  }
}

var options = document.querySelectorAll('input.option');
for(var i = 0; i < options.length; i++) {
  options[i].onclick = function() {
    if(!this.checked) {
      const parentOfThisBox = this.parentNode;
      uncheckChildBox(parentOfThisBox);
    } else {
      const parentWithClass = this.closest('.nested');
      if(parentWithClass && this.checked) {
        const parentLi = parentWithClass.parentNode;
          if(parentLi && parentLi.children[0]) {
            checkParentBox(parentLi.children[0]);
          }
       }   
    }
  }
}
