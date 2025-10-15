// Function to submit tasks to the task system
async function submitTask(taskFunction, taskName, taskParams) {
    const response = await fetch(window.global_var['task_submit_url'], {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            function: taskFunction,
            name: taskName,
            kwargs: taskParams
        })
    });

    return await response.json();
}