let mode = "pomodoro";
let isRunning = false;
let timerInterval = null;
let timeLeft = 25 * 60;  

const modeDurations = { 
  pomodoro: 25 * 60, 
  short: 5 * 60,    
  long: 15 * 60      
};

// Update the timer display
function updateTimerDisplay() {
  const m = String(Math.floor(timeLeft / 60)).padStart(2, '0');
  const s = String(timeLeft % 60).padStart(2, '0');
  document.getElementById('timer').textContent = `${m}:${s}`;
}

// Set the mode (Focus, Short, Long)
function setMode(newMode) {
  mode = newMode;
  timeLeft = modeDurations[mode]; 
  resetTimer();
  highlightModeButton();
}

// Highlight the active mode button
function highlightModeButton() {
  document.querySelectorAll('.tab').forEach(btn => btn.classList.remove('active-tab'));
  const active = document.getElementById(`mode-${mode}`);
  active.classList.add('active-tab');
}

// Toggle the timer (Start/Pause)
function toggleTimer() {
  const startBtn = document.getElementById('startBtn');
  if (!isRunning) {
    isRunning = true;
    startBtn.textContent = 'Pause';
    timerInterval = setInterval(() => {
      if (timeLeft > 0) {
        timeLeft--;
        updateTimerDisplay();
      } else {
        clearInterval(timerInterval);
        isRunning = false;
        startBtn.textContent = 'Start';
        alert("Time's up");
      }
    }, 1000);
  } else {
    clearInterval(timerInterval);
    isRunning = false;
    startBtn.textContent = 'Start';
  }
}

// Toggle Task completion (without pausing the timer)
function toggleTask(taskId) {
  const togglePopup = document.getElementById("toggleTaskPopup");
  togglePopup.classList.remove("hidden");

  document.getElementById("confirmToggleButton").onclick = function() {
    toggleTaskComplete(taskId);
    togglePopup.classList.add("hidden");
  };

  document.getElementById("cancelToggleButton").onclick = function() {
    togglePopup.classList.add("hidden");
  };
}

// Delete Task and Confirm Deletion
function deleteTask(taskId) {
  const deletePopup = document.getElementById("deleteTaskPopup");
  deletePopup.classList.remove("hidden");

  document.getElementById("confirmDeleteButton").onclick = function() {
    deleteTaskFromList(taskId);
    deletePopup.classList.add("hidden");
  };

  document.getElementById("cancelDeleteButton").onclick = function() {
    deletePopup.classList.add("hidden");
  };
}

// Handle Task Deletion from DOM
function deleteTaskFromList(taskId) {
  fetch(`/delete_task/${taskId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({})
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      const el = document.getElementById(`task-${taskId}`);
      if (el) el.remove();
    } else {
      console.error("Error deleting task:", data.error);
    }
  })
  .catch(err => console.error("Error:", err));
}

// Mark Task as Complete (without pausing the timer)
function toggleTaskComplete(taskId) {
  fetch(`/toggle_task/${taskId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({})
  })
  .then(r => r.json())
  .then(data => {
    if (!data.success) {
      console.error("Error toggling task:", data.error);
      return;
    }

    const taskElement = document.getElementById(`task-${taskId}`);
    if (!taskElement) return;

    const btn = taskElement.querySelector('form button');
    if (btn) {
      if (data.completed) {
        btn.innerHTML = '<span class="h-3 w-3 rounded-full bg-accent-500 inline-block"></span>';
      } else {
        btn.innerHTML = '';
      }
    }

    // toggle line-through on description
    const desc = taskElement.querySelector('.task-desc');
    if (desc) {
      if (data.completed) {
        desc.classList.add('line-through', 'text-slate-400');
      } else {
        desc.classList.remove('line-through', 'text-slate-400');
      }
    }

    // move between lists
    if (data.completed) {
      document.getElementById('completedTaskList').appendChild(taskElement);
    } else {
      document.getElementById('taskList').appendChild(taskElement);
    }
  })
  .catch(err => console.error("Error:", err));
}

// Add New Task
function addTask(event) {
  event.preventDefault();
  const description = document.getElementById("taskDescription").value.trim();
  if (!description) return;

  fetch("/add_task", {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({ description, estimated: 1 })
  })
  .then(r => r.json())
  .then(data => {
    if (data.id) {
      const taskList = document.getElementById("taskList");
      const newTask = document.createElement("div");
      newTask.className = "flex items-center justify-between bg-white/70 rounded-xl border border-slate-200 p-3";
      newTask.id = `task-${data.id}`;
      newTask.innerHTML = `
        <div class="flex items-center gap-3">
          <form id="toggle-task-${data.id}" class="task-form" data-task-id="${data.id}">
            <button type="button" class="h-5 w-5 rounded-full border border-slate-300 flex items-center justify-center" onclick="toggleTask(${data.id})"></button>
          </form>
          <span class="task-desc">${data.description}</span>
          ${data.assigned_by_admin ? `
            <span class="ml-2 inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-700" title="Assigned by admin">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2l7 3v6c0 5-3.8 8.6-7 9-3.2-.4-7-4-7-9V5l7-3z"/>
              </svg>
              admin
            </span>` : ``}
        </div>
        <form id="delete-task-${data.id}" class="task-form" data-task-id="${data.id}">
          <button type="button" onclick="deleteTask(${data.id})" class="text-slate-500 hover:text-red-600" title="Delete">Delete</button>
        </form>
      `;
      taskList.appendChild(newTask);
      document.getElementById("taskDescription").value = "";
      closeTaskModal();
    }
  })
  .catch(err => console.error("Error adding task:", err));
}


document.getElementById("addTaskForm").addEventListener("submit", addTask);

function resetTimer() { 
  clearInterval(timerInterval); 
  isRunning = false; 
  timeLeft = modeDurations[mode]; 
  updateTimerDisplay(); 
  document.getElementById('startBtn').textContent = 'Start'; 
}

function openTaskModal() { 
  document.getElementById('taskModal').classList.remove('hidden'); 
}

function closeTaskModal() { 
  document.getElementById('taskModal').classList.add('hidden'); 
}

highlightModeButton();
updateTimerDisplay();
