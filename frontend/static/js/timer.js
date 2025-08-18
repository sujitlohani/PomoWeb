let mode = "pomodoro";
let isRunning = false;
let timerInterval = null;
let timeLeft = 25 * 60;  // Default Focus time

const modeDurations = { 
  pomodoro: 25 * 60, // Focus
  short: 5 * 60,     // Short Break
  long: 15 * 60      // Long Break
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
  timeLeft = modeDurations[mode]; // Set the time left according to mode
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
    // No timer interaction here, just toggle the task completion
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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      document.getElementById(`task-${taskId}`).remove();
    } else {
      console.error("Error deleting task:", data.error);
    }
  })
  .catch(error => console.error("Error:", error));
}

// Mark Task as Complete (without pausing the timer)
function toggleTaskComplete(taskId) {
  fetch(`/toggle_task/${taskId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      const taskElement = document.getElementById(`task-${taskId}`);
      taskElement.classList.toggle('line-through', data.completed);
      taskElement.querySelector('span').classList.toggle('bg-accent-500', data.completed);

      // Move task to completed section
      const completedTaskList = document.getElementById("completedTaskList");
      completedTaskList.appendChild(taskElement); // Move to the Completed section
    } else {
      console.error("Error toggling task:", data.error);
    }
  })
  .catch(error => console.error("Error:", error));
}

// Add New Task
function addTask(event) {
  event.preventDefault();
  const description = document.getElementById("taskDescription").value.trim();
  if (!description) return;

  fetch("/add_task", {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      description: description,
      estimated: 1
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.id) {
      const taskList = document.getElementById("taskList");
      const newTask = document.createElement("div");
      newTask.classList.add("flex", "items-center", "justify-between", "bg-white/70", "rounded-xl", "border", "border-slate-200", "p-3");
      newTask.id = `task-${data.id}`;
      newTask.innerHTML = ` 
        <div class="flex items-center gap-3">
          <form id="toggle-task-${data.id}" class="task-form" data-task-id="${data.id}">
            <button type="button" class="h-5 w-5 rounded-full border border-slate-300 flex items-center justify-center" onclick="toggleTask(${data.id})">
              <span class="h-3 w-3 rounded-full inline-block"></span>
            </button>
          </form>
          <span>${data.description}</span>
        </div>
        <form id="delete-task-${data.id}" class="task-form" data-task-id="${data.id}">
          <button type="button" onclick="deleteTask(${data.id})" class="text-slate-500 hover:text-red-600" title="Delete">Delete</button>
        </form>
      `;
      taskList.appendChild(newTask);
      closeTaskModal();
    }
  })
  .catch(error => console.error("Error adding task:", error));
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
