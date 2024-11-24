// Misc. JS Scripts


// Function to upload a file to the server
function uploadFile(event) {
    const file = event.target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    fetch('/add_materials_from_csv', {
        method: 'POST',
        body: formData
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
    });
}