var select = document.getElementById('reference_for_species');
var value = select.options[select.selectedIndex].value;
var selected = document.getElementById('hidden_reference_for_species');
selected.value = value;