document.addEventListener('DOMContentLoaded', function () {
    const classSelect = document.getElementById('class_id');
    const subjectSelect = document.getElementById('subject_id');

    if (classSelect && subjectSelect) {

        function filterSubjects() {
            const selectedClassId = classSelect.value;
            const subjectOptions = subjectSelect.querySelectorAll('option');

            let currentSelectedValid = false;

            subjectOptions.forEach(option => {
                const subjectClassId = option.getAttribute('data-class-id');

                // Always show the placeholder option
                if (option.value === "") {
                    option.style.display = "";
                    option.disabled = false;
                    return;
                }

                // Only show subjects if a class is selected AND the ID matches
                if (selectedClassId !== "" && subjectClassId === selectedClassId) {
                    option.style.display = "";
                    option.disabled = false;
                    if (option.selected) currentSelectedValid = true;
                } else {
                    option.style.display = "none";
                    option.disabled = true;
                }
            });

            // If the currently selected subject is now hidden (or if no class selected), reset selection
            // We only reset if we actually have a value selected that is now invalid
            if (!currentSelectedValid && subjectSelect.value !== "") {
                subjectSelect.value = "";
            }
        }

        // Run on load to set initial state
        filterSubjects();

        // Run on change
        classSelect.addEventListener('change', filterSubjects);
    }
});
