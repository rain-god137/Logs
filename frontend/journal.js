import { Crepe } from '@milkdown/crepe';
import '@milkdown/crepe/theme/common/style.css';
import '@milkdown/crepe/theme/frame.css';
import { Plugin } from 'prosemirror-state';
import { getMarkdown } from '@milkdown/utils' ;
import axios from 'axios';



document.addEventListener('DOMContentLoaded', async function() {
    
    // This is the div which will be updated everytime any action is performed related to files
    const toRefresh = document.getElementById('toUpdate');


    // File creation shenanigans
    const fileCreator = document.getElementById('fileCreator');

    fileCreator.addEventListener('keydown', async function(event) {
        if (event.key === 'Enter') {
           const fileName = fileCreator.value.trim();
            if (!fileName) {
                fileCreator.value = "";
                return;
            }

            try {
                // Properly await the axios call and capture the response
                await axios.post('/api/journal/create', { filename: fileName })
                .then(respo => {
                    toRefresh.innerHTML = respo.data;
                });

                // Clear any previous error and reload on success
                const showError = document.getElementById('fError');
                if (showError) showError.innerHTML = "";

            } catch (error) {
                // axios throws error then handle a 400 (file exists) specifically
                if (error.response && error.response.status === 400) {
                    const showError = document.getElementById('fError');
                    if (showError) showError.innerHTML = "<p style='color: red;'>File already exists!</p>";
                } else {
                    console.error('Error creating file:', error);
                }
            }

            fileCreator.value = ""; 
        }
    });

    // File appearence shenanigans
    let savedContent = '';
    const input = document.getElementById('fileInput'); 
    const nameDisplay = document.getElementById('nameDisplay');

    let crepe = null;

    document.getElementById('toUpdate').addEventListener('click', async function(event) {
        const btn = event.target.closest('.fNames');
        if (!btn) return;

        try {
            const fileName = btn.dataset.filename || btn.textContent.trim();
            const fileResponse = await axios.get('/api/journal/get', {params: { filename: fileName }});
            savedContent = fileResponse.data.content;

            input.innerHTML = '';  // Clear previous editor content
            nameDisplay.innerHTML = fileName; // Display the file name
            document.getElementById('saveBtn').innerHTML =
                '<span ' +
                'onmouseover="this.style.backgroundColor=\'#3a2b54\'" ' +
                'onclick="this.style.backgroundColor=\'#a06afd87\'" ' +
                'onmouseout="this.style.backgroundColor=\'transparent\'" ' +
                'style="border-radius: 4px;" ' +
                'class="material-symbols-outlined text-neon-lavender">' +
                'save</span>'
            ;

            // Create the editor
            const crepe = new Crepe({
            root: input,
            defaultValue: savedContent || '',
            editorViewOptions: {
                plugins: [enforceTopHeading, lockTopHeading],
            },
            });

            // Mount the editor
            await crepe.create();

            // TaskNotes Saving Shenanigans
            document.getElementById('saveBtn').addEventListener('click', async function() {    

                const markdown = crepe.editor.action(getMarkdown());
                axios.post('/api/journal', {
                    content: markdown,
                    filename: fileName},
                    { headers: {
                        'Content-Type': 'application/json'
                        }
                }).then(showPopUp());


            
            });

            input.addEventListener('keydown', async function(e) {
                if (e.ctrlKey && e.key.toLowerCase() === 's') {
                    e.preventDefault();

                    const markdownn = crepe.editor.action(getMarkdown());
                    axios.post('/api/journal', {
                    content: markdownn,
                    filename: fileName},
                    { headers: {
                        'Content-Type': 'application/json'
                        }
                    }).then(showPopUp());


                }
            });
            
            
            


        } catch (error) {
            console.error('Error fetching file content:', error);
        }
        
    });

    // File deletion shenanigans
    document.getElementById('toUpdate').addEventListener('click', async function(event) {
        const delBtn = event.target.closest('.deleteBtn');
        if (!delBtn) return;

        try {
            const fileName = delBtn.dataset.filename || delBtn.textContent.trim();
            await axios.post('/api/journal/delete', { filename: fileName})
            
            .then(async function (responsee) {
                input.innerHTML = '<div class="flex items-center justify-center h-full w-full text-gray-400 italic select-none">Select a file to view its content.</div>';
                document.getElementById('savePopUp').style.opacity = 0;
                document.getElementById('nameDisplay').innerHTML = '';
                document.getElementById('saveBtn').innerHTML = '';

                toRefresh.innerHTML = responsee.data;
            });


        } catch (error) {
            console.error('Error deleting file:', error);
        }
    });
    

    // Text editor shenanigans

    const enforceTopHeading = new Plugin({
    filterTransaction(tr) {
        const doc = tr.doc;

        // Must have a first node
        if (!doc.firstChild) return false;

        // First node must be heading
        if (doc.firstChild.type.name !== 'heading') {
            return false;
        }

        return true;
    },
    });

    const lockTopHeading = new Plugin({
    filterTransaction(tr, state) {
        const doc = tr.doc;
        const first = doc.firstChild;

        // Must exist
        if (!first) return false;

        // Must be a heading
        if (first.type.name !== 'heading') return false;

        // Must not be empty
        const text = first.textContent.trim();
        if (text.length === 0) return false;

        return true;
    },
    });    

    // Function to display the popUp once the contents are saved.
    function showPopUp() {

        const popUp = document.getElementById('savePopUp');

        popUp.classList.add('show');

        setTimeout(() => {
            popUp.classList.remove('show');
        }, 1000);

    };
}) 
