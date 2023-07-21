function createTableFromObjects(data) {
    const table = document.createElement('table');
    const headerRow = document.createElement('tr');
    
    // Create table header row
    const keys = Object.keys(data[0]);
    for (const key of keys) {
      const headerCell = document.createElement('th');
      headerCell.textContent = key;
      headerRow.appendChild(headerCell);
    }
    table.appendChild(headerRow);
  
    // Create table data rows
    for (const obj of data) {
      const dataRow = document.createElement('tr');
      for (const key of keys) {
        const dataCell = document.createElement('td');
        dataCell.textContent = obj[key];
        dataRow.appendChild(dataCell);
      }
      table.appendChild(dataRow);
    }
  
    return table;
  }