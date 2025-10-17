function openFile() {
  window.pywebview.api.open_file_dialog().then(path => {
    document.getElementById('result').innerText = path || "No file selected";
  });
}

function openFolder() {
  window.pywebview.api.open_folder_dialog().then(folderPath => {
    document.getElementById('result').innerText = folderPath || "No folder selected";
  });
}