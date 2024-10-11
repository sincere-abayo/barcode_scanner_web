   
   
 document.addEventListener('DOMContentLoaded', function() {
 const searchInput = document.getElementById('searchInput');
 const searchButton = document.getElementById('searchButton');

 function performSearch() {
    const searchTerm = searchInput.value.toLowerCase();
    const rows = tableRow.getElementsByTagName('tr');

    for (let row of rows) {
        const cells = row.getElementsByTagName('td');
        let found = false;

        for (let cell of cells) {
            if (cell.textContent.toLowerCase().includes(searchTerm)) {
                found = true;
                break;
            }
        }

        row.style.display = found ? '' : 'none';
    }
}

searchInput.addEventListener('input', performSearch);
searchButton.addEventListener('click', performSearch);

 });