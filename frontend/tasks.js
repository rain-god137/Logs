import axios from 'axios';
import { Crepe } from '@milkdown/crepe';
import '@milkdown/crepe/theme/common/style.css';
import '@milkdown/crepe/theme/frame.css';
import '@milkdown/crepe/theme/common/style.css';
import '@milkdown/crepe/theme/common/style.css';
import { getMarkdown } from '@milkdown/utils' ;
import flatpickr from 'flatpickr';

document.addEventListener('DOMContentLoaded', () => {

    // Date selection shenanigans
    const datepicker = flatpickr("#date-picker", {});

        // styling the date picker
    const calendarContainer = datepicker.calendarContainer;
    const calendarMonthNav = datepicker.monthNav;
    const calendarNextMonthNav = datepicker.nextMonthNav;
    const calendarPrevMonthNav = datepicker.prevMonthNav;
    const calendarDaysContainer = datepicker.daysContainer;
    
    calendarContainer.className = `${calendarContainer.className} bg-white p-4 border border-blue-gray-50 rounded-lg shadow-lg shadow-blue-gray-500/10 font-sans text-sm font-normal text-blue-gray-500 focus:outline-none break-words whitespace-normal`;
    calendarMonthNav.className = `${calendarMonthNav.className} flex items-center justify-between mb-2 mt-3 [&>div.flatpickr-month]:-translate-y-3`;
    calendarNextMonthNav.className = `${calendarNextMonthNav.className} absolute !top-2.5 !right-1.5 h-6 w-6 bg-transparent hover:bg-blue-gray-50 !p-1 rounded-md transition-colors duration-300`;
    calendarPrevMonthNav.className = `${calendarPrevMonthNav.className} absolute !top-2.5 !left-1.5 h-6 w-6 bg-transparent hover:bg-blue-gray-50 !p-1 rounded-md transition-colors duration-300`;
    calendarDaysContainer.className = `${calendarDaysContainer.className} [&_span.flatpickr-day]:!rounded-md [&_span.flatpickr-day.selected]:!bg-gray-900 [&_span.flatpickr-day.selected]:!border-gray-900`;



    const dateInp = document.getElementById('date-picker')
    console.log(dateInp.value)
    dateInp.addEventListener('change', async function(e) {

        const d = new Date();
        const d1 = d.toISOString().split('T')[0];
        const selectedDate = e.target.value;
        console.log(selectedDate)
        const toRefresh = document.getElementById('toRefresh');


        try {
            const toRemove = document.getElementById('taskCreator');
            await axios.post('/api/task/date', {"date": selectedDate})
            .then(response => {
                toRefresh.innerHTML = response.data;
                if (d1 !== selectedDate)
                    toRemove.hidden = true;
                    
                
                else
                    toRemove.hidden = false;
            })
            .catch(error => {
                console.error("Error:", error);
            })

            updateCompletion();

        } catch (error) {
            console.error('Error!', error)
        }
    }); 

    // Tasks input sheanigans 
    const taskCreator = document.getElementById('taskCreator'); 
    taskCreator.addEventListener('keydown', async function(e) {

        const toRefresh = document.getElementById('toRefresh');
        if (e.key === 'Enter') {
            const taskName = taskCreator.value.trim();

            if (!taskName) {

                taskCreator.value = "";
                return;
                
            }

            try {
                const taskSend = await axios.post('api/task/create', {task: taskName})
                .then(response => {
                    toRefresh.innerHTML = response.data;
                })
            }

            catch (error){
                console.error('Error:', error);
            }

            taskCreator.value = "";
            updateCompletion();
            
        }
    });

    // Task Selection & Notes Display Shenanigans
    const noteInput = document.getElementById('taskNote');
    document.getElementById('toRefresh').addEventListener('click', async function(ev){
        const tBtn = ev.target.closest('.tasksClic');
    
        if (!tBtn) return;
    
        
        document.querySelector('.tasksClic.selected')?.classList.remove("selected");
        tBtn.classList.add("selected");

    
        const taskName = tBtn.dataset.taskname;
        const tid = tBtn.dataset.taskref;

        const noteresponse = await axios.get('/api/task/notes', {
            params: { name: taskName, id: tid }
            });

        const savedContent = noteresponse.data.note || `# ${taskName}`;

        try {

            noteInput.innerHTML = '';
            document.getElementById('editorHeader').innerHTML = taskName;
            document.getElementById('saveBtn').innerHTML =
                '<span ' +
                'onmouseover="this.style.backgroundColor=\'#3a2b54\'" ' +
                'onclick="this.style.backgroundColor=\'#a06afd87\'" ' +
                'onmouseout="this.style.backgroundColor=\'transparent\'" ' +
                'style="border-radius: 4px;" ' +
                'class="material-symbols-outlined text-neon-lavender">' +
                'save</span>'
            ;

            const crepe = new Crepe({
                root: noteInput,
                defaultValue: savedContent,
                theme: 'dark',
            });


            await crepe.create();

            // TaskNotes Saving Shenanigans
            document.getElementById('saveBtn').addEventListener('click', async function() {    

                const markdown = crepe.editor.action(getMarkdown());
                axios.post('/api/task/update', {
                    content: markdown,
                    id: tid},
                    { headers: {
                        'Content-Type': 'application/json'
                        }
                }).then(showPopUp());


            
            });

            noteInput.addEventListener('keydown', async function(e) {
                if (e.ctrlKey && e.key.toLowerCase() === 's') {
                    e.preventDefault();

                    const markdownn = crepe.editor.action(getMarkdown());
                    axios.post('/api/task/update', {
                    content: markdownn,
                    id: tid},
                    { headers: {
                        'Content-Type': 'application/json'
                        }
                    }).then(showPopUp());


                }
            });

            

        } catch (error) {
            console.error("Showing Error: ", error)
        }
        
    });

    
    // popUp on saveBtn
    document.getElementById('saveBtn').addEventListener('mouseenter', () => {
        const onHover = document.getElementById('onCursor');
        onHover.classList.add('show');
    });

    document.getElementById('saveBtn').addEventListener('mouseleave', () => {
        const onHover = document.getElementById('onCursor');
        onHover.classList.remove('show');
    });

    // Task completion Shenanigans
    document.getElementById('toRefresh').addEventListener('change', async function(e) {
        const checkBtn = e.target.closest('.cbx');
        
        console.log('checkbox clicked');
        if(!checkBtn) return;

        const id = checkBtn.dataset.taskref;
        let status = 0;
        if (checkBtn.checked) {
            status = 1;
        }

        else {
            status = 0;
        }

        try {
            await axios.post('/api/task/mark', {taskId : id, stat: status});
            updateCompletion();
            
        } catch (error) {
            console.error('Error marking status:', error)
        } 
    });


    // Task Deletion Shenanigans
    document.getElementById('toRefresh').addEventListener('click', async function(ev) {
        const dltBtn = ev.target.closest('.deleteBtns');

        if (!dltBtn) return;

        const toRefresh = document.getElementById('toRefresh');
        const dltId = dltBtn.dataset.taskref;
        const choosedDate = document.getElementById('date-picker').value
        await axios.post('/api/task/delete', {"id": dltId, "date": choosedDate})
        .then(response => {
            toRefresh.innerHTML = response.data;
            document.getElementById('taskNote').innerHTML = '<div class="flex items-center justify-center h-full w-full text-gray-400 italic select-none">Select a task to view its content.</div>';
            document.getElementById('savePopUp').style.opacity = 0;
            document.getElementById('editorHeader').innerHTML = '';
            document.getElementById('saveBtn').innerHTML = '';

            updateCompletion();
        })

    })

    // Time shenanigans
    function updateTime() {
        const now = new Date();
        const timeElement = document.getElementById('current-time');
        timeElement.dateTime = now.toISOString();
        timeElement.innerHTML = `${now.toLocaleTimeString(undefined, {hour12: false})}`;
    }

    setInterval(updateTime, 1000);
    updateTime();

    // Function to update the task completion thingy.
    async function updateCompletion() {
        const pickedDate = document.getElementById('date-picker').value
        await axios.get('/api/task/completion', {params: {"date": pickedDate}})
        .then(response => {
                const data = response.data;
                const total = data.tPending;
                const cmplte = data.tCompleted;

                const disp = `${cmplte}/${total}`;
                document.getElementById('cpndisplay').innerHTML = disp;
            })


        .catch(error => {
        console.error('Cannnot retrieve data:', error);
        });
    }

    // Function to display the popUp once the contents are saved.
    function showPopUp() {

        const popUp = document.getElementById('savePopUp');

        popUp.classList.add('show');

        setTimeout(() => {
            popUp.classList.remove('show');
        }, 1000);

    };
})
