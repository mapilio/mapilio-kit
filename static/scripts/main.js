document.addEventListener("DOMContentLoaded", function () {
    const logoutBtn = document.getElementById('logoutBtn');
    const dropArea = document.getElementById('drop-area');
    const fileList = document.getElementById('fileList').querySelector('ul');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropArea.classList.add('highlight');
    }

    function unhighlight(e) {
        dropArea.classList.remove('highlight');
    }

    function updateTotalImagesCount() {
        const totalImagesCount = fileList.querySelectorAll('li').length;
        document.getElementById('totalImagesCount').textContent = totalImagesCount;
    }

    dropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();

        let dt = e.dataTransfer;
        console.log("Files from Drop:", dt.files);

        let droppedFiles = dt.files; 


        handleFiles(droppedFiles);
        updateTotalImagesCount();


        let newFileList = new DataTransfer();

        for (let i = 0; i < fileInput.files.length; i++) {
            newFileList.items.add(fileInput.files[i]);
        }

        for (let i = 0; i < droppedFiles.length; i++) {
            newFileList.items.add(droppedFiles[i]);
        }
        fileInput.files = newFileList.files;
    }



    function isDuplicate(fileName) {
        let items = fileList.querySelectorAll('li');
        for (let i = 0; i < items.length; i++) {
            if (items[i].innerHTML.trim() === fileName.trim()) {
                return true;
            }
        }
        return false;
    }

    function handleFiles(droppedFiles) {
        [...droppedFiles].forEach(file => {
            if (!isDuplicate(file.name) && file.type.match('image.*')) {
                uploadFile(file);
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: `Please drop only image files, and make sure the file does not already exist in the list.`,
                    timer: 3000,
                    timerProgressBar: true,
                    showConfirmButton: false
                });
            }
        });
        updateTotalImagesCount();
    }

    const fileInput = document.getElementById('fileElem');

    fileInput.addEventListener('change', function () {
        let files = this.files;
        handleFiles(files);
    }, false);

    let addedFiles = [];

   function uploadFile(file) {
        let li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';

        let imageContainer = document.createElement('div');
        imageContainer.className = 'image-container';

        let previewImg = document.createElement('img');
        previewImg.className = 'preview-image float-start rounded me-2 img-fluid';
        previewImg.src = URL.createObjectURL(file);

        imageContainer.appendChild(previewImg);

        li.appendChild(imageContainer);

        let fileInfo = document.createElement('div');
        fileInfo.className = 'text-end';

        let fileNameSpan = document.createElement('span');
        fileNameSpan.textContent = file.name;
        fileNameSpan.className = 'text-center me-auto';
        fileInfo.appendChild(fileNameSpan);

        let deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-danger btn-sm ms-2';
        deleteBtn.textContent = 'Delete';
        deleteBtn.addEventListener('click', function () {
            let index = addedFiles.indexOf(file);
            if (index !== -1) {
                addedFiles.splice(index, 1);
            }
            li.remove();
            updateTotalImagesCount();
            removeFileFromInput(file);
        });
        fileInfo.appendChild(deleteBtn);

        li.appendChild(fileInfo);

        fileList.appendChild(li);

        addedFiles.push(file);
    }


    function removeFileFromInput(fileToRemove) {
        let newFileList = new DataTransfer();
        for (let i = 0; i < fileInput.files.length; i++) {
            if (fileInput.files[i] !== fileToRemove) {
                newFileList.items.add(fileInput.files[i]);
            }
        }
        fileInput.files = newFileList.files;
    }

    logoutBtn.addEventListener('click', function (event) {
        event.preventDefault();

        fetch('/logout', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Logged Out',
                        text: 'You have been successfully logged out!',
                        timer: 2000,
                        timerProgressBar: true,
                        showConfirmButton: false
                    }).then(() => {
                        window.location.href = '/login';
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: data.message,
                        timer: 2000,
                        timerProgressBar: true,
                        showConfirmButton: false
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    });

    const uploadBtn = document.getElementById('uploadBtn');
    uploadBtn.addEventListener('click', function () {
        let files = fileInput.files;
        console.log("Selected files:", files);
        let formData = new FormData();

        for (let i = 0; i < files.length; i++) {
            formData.append('file', files[i]);
        }
        if (files.length === 0) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Please select a file to upload.',
                timer: 2000,
                timerProgressBar: true,
                showConfirmButton: false
            });
            return;
        }

        Swal.fire({
            icon: 'info',
            title: 'Uploading...',
            text: 'Please wait while we upload your file.',
            showConfirmButton: false,
            allowOutsideClick: false,
            allowEscapeKey: false,
            allowEnterKey: false
        });

        fetch('/image-upload', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fileList.innerHTML = '';
                    fileInput.value = '';
                    updateTotalImagesCount();
                    Swal.fire({
                        icon: 'success',
                        title: "Upload successfully done!",
                        html: "<table style='margin: 0 auto;'> \
                                  <tr> \
                                      <td style='text-align: left;'>Total images:</td> \
                                      <td style='padding-left: 10px; font-weight: bold;'>" + data.total_images + "</td> \
                                  </tr> \
                                  <tr> \
                                      <td style='text-align: right;'>Processed images:</td> \
                                      <td style='padding-left: 10px; font-weight: bold;'>" + data.processed_images + "</td> \
                                  </tr> \
                                  <tr> \
                                      <td style='text-align: left;'>Failed images:</td> \
                                      <td style='padding-left: 10px; font-weight: bold;'>" + data.failed_images + "</td> \
                                  </tr> \
                              </table>",
                        footer: "Thanks for contributions to Mapilio 🎉",
                        timerProgressBar: true,
                        showConfirmButton: false
                    })
                                 
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: data.message,
                        timer: 2000,
                        timerProgressBar: true,
                        showConfirmButton: false
                    });
                }
            })
            .catch(data => {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.message,
                    timer: 2000,
                    timerProgressBar: true,
                    showConfirmButton: false
                });
            });
    });

    const removeAllBtn = document.getElementById('removeAllBtn');

    removeAllBtn.addEventListener('click', function () {
        if (fileList.innerHTML === '' && fileInput.value === '') {
            Swal.fire({
                icon: 'warning',
                title: 'Warning',
                text: 'The file list is already empty!',
                timer: 2000,
                timerProgressBar: true,
                showConfirmButton: false
            });
        } else {
            fileList.innerHTML = '';
            fileInput.value = '';
            updateTotalImagesCount();
        }
    });
});