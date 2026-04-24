let currentSectionId = null;
        let currentTimeField = null;
        let currentEditScheduleId = null;
        let selectedHour = 7;
        let selectedMinute = 30;
        let selectedPeriod = 'AM';
        let currentSchedules = []; // Store current schedules for validation
        let facultyScheduleCache = {}; // Cache schedule data by faculty ID

        // Tab switching
        function switchTab(tabName) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            document.querySelector('.tab-btn').classList.add('active');
            document.getElementById('manualTab').classList.add('active');
        }

        // Modal management
        function openScheduleModal() {
            try {
                console.log('DEBUG: openScheduleModal() called');
                
                // Reset form fields
                const courseSelect = document.getElementById('course_select');
                const facultySelect = document.getElementById('faculty_select');
                const sectionSelect = document.getElementById('section_select');
                const roomSelect = document.getElementById('room_select');
                
                if (!courseSelect || !facultySelect || !sectionSelect || !roomSelect) {
                    console.error('ERROR: Required form elements not found', {
                        courseSelect: !!courseSelect,
                        facultySelect: !!facultySelect,
                        sectionSelect: !!sectionSelect,
                        roomSelect: !!roomSelect
                    });
                    showAlert('Error: Form elements not found. Please reload the page.', 'error');
                    return;
                }
                
                courseSelect.value = '';
                facultySelect.value = '';
                sectionSelect.value = currentSectionId || '';
                roomSelect.value = '';
                
                // Reset day checkboxes (new multiselect checkbox implementation)
                document.querySelectorAll('input[name="day"]').forEach(checkbox => {
                    checkbox.checked = false;
                });
                updateDayDropdownLabel(); // Reset dropdown button text
                
                const startTime = document.getElementById('start_time');
                const endTime = document.getElementById('end_time');
                if (startTime && endTime) {
                    startTime.value = '07:30';
                    endTime.value = '08:30';
                }
                
                const durationDisplay = document.getElementById('duration-display');
                const courseReqInfo = document.getElementById('course-requirements-info');
                const courseWarning = document.getElementById('course-warning');
                
                if (durationDisplay) durationDisplay.style.display = 'none';
                if (courseReqInfo) courseReqInfo.style.display = 'none';
                if (courseWarning) courseWarning.style.display = 'none';
                
                if (startTime) setTimeDisplay('start_time');
                if (endTime) setTimeDisplay('end_time');
                
                // Initialize day and faculty filtering
                console.log('DEBUG: Calling filterAvailableDays...');
                filterAvailableDays();
                
                console.log('DEBUG: Calling filterAvailableInstructors...');
                filterAvailableInstructors('faculty_select');
                
                console.log('DEBUG: Calling filterCourses...');
                filterCourses('course_select');
                
                console.log('DEBUG: Calling switchTab...');
                switchTab('manual');
                
                console.log('DEBUG: Opening modal...');
                openModal('scheduleModal');
                
                console.log('DEBUG: openScheduleModal() completed successfully');
            } catch (error) {
                console.error('ERROR in openScheduleModal():', error);
                console.error('Stack:', error.stack);
                showAlert(`Error opening schedule modal: ${error.message}`, 'error');
            }
        }

        function openModal(modalId) {
            document.getElementById(modalId).style.display = 'block';
        }

        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }

        // Multi-select dropdown handler
        function toggleDayDropdown(event) {
            event.preventDefault();
            const menu = document.getElementById('dayDropdownMenu');
            const button = document.getElementById('dayDropdownButton');
            menu.classList.toggle('open');
            button.classList.toggle('open');
        }

        // Update dropdown button label based on selected days
        function updateDayDropdownLabel() {
            const dayCheckboxes = document.querySelectorAll('input[name="day"]:checked');
            const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const button = document.getElementById('dayDropdownButton');
            
            if (dayCheckboxes.length === 0) {
                button.innerHTML = '<span style="color: #999;">Select days...</span>';
            } else if (dayCheckboxes.length === 6) {
                button.innerHTML = '<span>All days (Monday - Saturday)</span>';
            } else {
                const selectedDays = Array.from(dayCheckboxes)
                    .map(cb => dayNames[parseInt(cb.value)])
                    .join(', ');
                button.innerHTML = `<span>${selectedDays}</span>`;
            }
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', function(event) {
            const dropdown = document.querySelector('.multiselect-dropdown');
            if (dropdown && !dropdown.contains(event.target)) {
                const menu = document.getElementById('dayDropdownMenu');
                const button = document.getElementById('dayDropdownButton');
                if (menu) {
                    menu.classList.remove('open');
                    button.classList.remove('open');
                }
            }
        });

        function handleSectionSelectChange() {
            const sectionSelect = document.getElementById('section_select');
            if (!sectionSelect) return;

            const selectedOption = sectionSelect.selectedOptions[0];
            if (!selectedOption || !selectedOption.value) return;

            const sectionId = selectedOption.value;
            const sectionName = selectedOption.dataset.sectionName || selectedOption.textContent;
            const curriculum = selectedOption.dataset.sectionCurriculum || '';

            if (sectionId && String(sectionId) !== String(currentSectionId)) {
                loadScheduleView(sectionId, sectionName, curriculum);
            }
        }

        // Filter courses based on selected section
        function filterCourses(courseSelectId) {
            const sectionSelect = document.getElementById('section_select');
            const courseSelect = document.getElementById(courseSelectId);
            
            console.log('DEBUG filterCourses called with:', courseSelectId);
            
            if (!sectionSelect || !courseSelect) return;
            
            const selectedSectionOption = sectionSelect.selectedOptions[0];
            if (!selectedSectionOption || !selectedSectionOption.value) {
                console.log('  No section selected, showing all courses');
                // If no section selected, show all courses
                courseSelect.querySelectorAll('option').forEach(option => {
                    if (option.value === '') {
                        option.disabled = false;
                        option.hidden = false;
                    } else {
                        option.disabled = false;
                        option.hidden = false;
                    }
                });
                return;
            }
            
            const sectionCurriculumId = selectedSectionOption.dataset.curriculumId;
            const sectionYearLevel = selectedSectionOption.dataset.yearLevel;
            const sectionSemester = selectedSectionOption.dataset.semester;
            const sectionId = selectedSectionOption.value;
            
            console.log('  Section selected:', { sectionId, sectionCurriculumId, sectionYearLevel, sectionSemester });
            
            // Filter course options to match section criteria
            courseSelect.querySelectorAll('option').forEach(option => {
                if (option.value === '') {
                    option.disabled = false;
                    option.hidden = false;
                    return;
                }
                
                const courseCurriculumId = option.dataset.curriculumId;
                const courseYearLevel = option.dataset.yearLevel;
                const courseSemester = option.dataset.semester;
                const courseId = option.value;
                const courseCode = option.dataset.courseCode;
                
                // Course matches section criteria
                const matches = (courseCurriculumId === sectionCurriculumId && 
                                 courseYearLevel === sectionYearLevel && 
                                 courseSemester === sectionSemester);
                
                console.log(`  Checking course ${courseCode} (${courseId}):`, { courseCurriculumId, courseYearLevel, courseSemester, matches });
                
                if (!matches) {
                    console.log(`    HIDING: criteria mismatch`);
                    option.disabled = true;
                    option.hidden = true;
                    return;
                }
                
                // Check if course has all its hours allocated
                const lectureHours = parseInt(option.dataset.lectureHours) || 0;
                const labHours = parseInt(option.dataset.laboratoryHours) || 0;
                
                const courseHours = getCourseHoursInSection(courseId, sectionId);
                
                console.log(`    Hours: lecture=${lectureHours}/${courseHours.lecture}, lab=${labHours}/${courseHours.lab}`);
                
                const isComplete = (lectureHours === 0 || courseHours.lecture >= lectureHours) &&
                                  (labHours === 0 || courseHours.lab >= labHours);
                
                console.log(`    isComplete = (${lectureHours}===0 || ${courseHours.lecture}>=${lectureHours}) && (${labHours}===0 || ${courseHours.lab}>=${labHours}) = ${isComplete}`);
                
                if (isComplete && lectureHours > 0 && labHours > 0) {
                    console.log(`    HIDING: course complete`);
                    option.disabled = true;
                    option.hidden = true;
                    option.textContent = `${option.dataset.originalText || option.textContent} (Complete)`;
                } else {
                    console.log(`    SHOWING`);
                    option.disabled = false;
                    option.hidden = false;
                }
            });
            
            // Clear the course selection if currently selected course doesn't match
            if (courseSelect.value) {
                const selectedCourseOption = courseSelect.selectedOptions[0];
                if (selectedCourseOption && selectedCourseOption.hidden) {
                    console.log('  Selected course is hidden, clearing selection');
                    courseSelect.value = '';
                    document.getElementById('course-requirements-info').style.display = 'none';
                    document.getElementById('course-warning').style.display = 'none';
                }
            }
        }

        // Get total hours used for a course in a section, EXCLUDING a specific schedule
        function getCourseHoursInSectionExcluding(courseId, sectionId, excludeScheduleId) {
            let lectureHours = 0;
            let labHours = 0;
            
            currentSchedules.forEach(schedule => {
                // Skip the schedule we're excluding (editing)
                // Handle both string and number IDs
                if (String(schedule.id) === String(excludeScheduleId)) {
                    return;
                }
                
                if (schedule.course_id == courseId && schedule.section_id == sectionId) {
                    const duration = schedule.duration || 0;
                    const durationHours = duration / 60;
                    
                    if (schedule.room_type === 'lecture') {
                        lectureHours += durationHours;
                    } else if (schedule.room_type === 'laboratory') {
                        labHours += durationHours;
                    } else if (schedule.room_type === null || schedule.room_type === undefined) {
                        // If room_type is not set, count as lecture by default (can be adjusted based on room)
                        console.warn('Schedule has no room_type assigned:', schedule);
                        lectureHours += durationHours;
                    }
                }
            });
            
            return { lecture: lectureHours, lab: labHours };
        }

        // Get total hours used for a course in a section
        function getCourseHoursInSection(courseId, sectionId) {
            let lectureHours = 0;
            let labHours = 0;
            
            console.log('DEBUG getCourseHoursInSection:', { courseId, sectionId, schedulesCount: currentSchedules.length });
            
            currentSchedules.forEach(schedule => {
                console.log('  Checking schedule:', { 
                    scheduleId: schedule.id, 
                    course_id: schedule.course_id, 
                    courseId: courseId, 
                    match: schedule.course_id == courseId,
                    section_id: schedule.section_id,
                    sectionId: sectionId,
                    room_type: schedule.room_type,
                    duration: schedule.duration
                });
                
                if (schedule.course_id == courseId && schedule.section_id == sectionId) {
                    const duration = schedule.duration || 0;
                    const durationHours = duration / 60;
                    console.log('    MATCHED! room_type:', schedule.room_type, 'duration:', duration);
                    
                    if (schedule.room_type === 'lecture') {
                        lectureHours += durationHours;
                        console.log('    Added to lecture:', durationHours, 'total lecture:', lectureHours);
                    } else if (schedule.room_type === 'laboratory') {
                        labHours += durationHours;
                        console.log('    Added to lab:', durationHours, 'total lab:', labHours);
                    } else if (schedule.room_type === null || schedule.room_type === undefined) {
                        // If room_type is not set, count as lecture by default
                        console.warn('WARNING: Schedule has no room_type assigned:', schedule);
                        lectureHours += durationHours;
                        console.log('    Added to lecture (no room_type):', durationHours, 'total lecture:', lectureHours);
                    } else {
                        console.log('    WARNING: room_type is neither lecture nor laboratory:', schedule.room_type);
                    }
                }
            });
            
            console.log('  RESULT:', { lecture: lectureHours, lab: labHours });
            return { lecture: lectureHours, lab: labHours };
        }

        // Show course requirements
        function showCourseRequirements(mode = '') {
            const courseSelectId = mode === 'edit' ? 'edit_course_select' : 'course_select';
            const courseSelect = document.getElementById(courseSelectId);
            const infoPrefix = mode === 'edit' ? 'edit_' : '';
            
            if (!courseSelect || !courseSelect.value) {
                document.getElementById(infoPrefix + 'course-requirements-info').style.display = 'none';
                document.getElementById(infoPrefix + 'course-warning').style.display = 'none';
                return;
            }
            
            const selectedOption = courseSelect.selectedOptions[0];
            const lectureHours = parseInt(selectedOption.dataset.lectureHours) || 0;
            const labHours = parseInt(selectedOption.dataset.laboratoryHours) || 0;
            
            if (lectureHours === 0 && labHours === 0) {
                document.getElementById(infoPrefix + 'course-requirements-info').style.display = 'none';
                return;
            }
            
            const sectionSelect = document.getElementById('section_select');
            const sectionId = sectionSelect ? sectionSelect.value : null;
            const courseId = courseSelect.value;
            
            if (!sectionId) {
                document.getElementById(infoPrefix + 'course-requirements-info').style.display = 'none';
                return;
            }
            
            // Use the excluding function if in edit mode
            const courseHours = mode === 'edit' 
                ? getCourseHoursInSectionExcluding(courseId, sectionId, currentEditScheduleId)
                : getCourseHoursInSection(courseId, sectionId);
            
            const lecRemaining = Math.max(0, lectureHours - courseHours.lecture);
            const labRemaining = Math.max(0, labHours - courseHours.lab);
            
            document.getElementById(infoPrefix + 'lec-required').textContent = lectureHours;
            document.getElementById(infoPrefix + 'lec-used').textContent = courseHours.lecture.toFixed(1);
            document.getElementById(infoPrefix + 'lec-remaining').textContent = lecRemaining.toFixed(1);
            
            document.getElementById(infoPrefix + 'lab-required').textContent = labHours;
            document.getElementById(infoPrefix + 'lab-used').textContent = courseHours.lab.toFixed(1);
            document.getElementById(infoPrefix + 'lab-remaining').textContent = labRemaining.toFixed(1);
            
            // Hide lecture or lab rows if not required
            if (lectureHours === 0) {
                document.getElementById(infoPrefix + 'lec-hours').style.display = 'none';
            } else {
                document.getElementById(infoPrefix + 'lec-hours').style.display = 'block';
            }
            
            if (labHours === 0) {
                document.getElementById(infoPrefix + 'lab-hours').style.display = 'none';
            } else {
                document.getElementById(infoPrefix + 'lab-hours').style.display = 'block';
            }
            
            document.getElementById(infoPrefix + 'course-requirements-info').style.display = 'block';
        }

        // Validate course-room match
        function validateCourseRoomMatch() {
            const courseSelect = document.getElementById('course_select');
            const roomSelect = document.getElementById('room_select');
            const warningDiv = document.getElementById('course-warning');
            
            console.log('DEBUG validateCourseRoomMatch called');
            
            if (!courseSelect.value || !roomSelect.value) {
                console.log('  Missing course or room value');
                warningDiv.style.display = 'none';
                return;
            }
            
            const selectedOption = courseSelect.selectedOptions[0];
            const lectureHours = parseInt(selectedOption.dataset.lectureHours) || 0;
            const labHours = parseInt(selectedOption.dataset.laboratoryHours) || 0;
            
            const roomOption = roomSelect.selectedOptions[0];
            const roomType = roomOption.dataset.roomType;
            
            const sectionSelect = document.getElementById('section_select');
            const sectionId = sectionSelect ? sectionSelect.value : null;
            const courseId = courseSelect.value;
            
            console.log('  Values:', { lectureHours, labHours, roomType, sectionId, courseId });
            
            if (!sectionId) {
                console.log('  No section ID');
                warningDiv.style.display = 'none';
                return;
            }
            
            const courseHours = getCourseHoursInSection(courseId, sectionId);
            const startTime = document.getElementById('start_time')?.value;
            const endTime = document.getElementById('end_time')?.value;
            
            console.log('  Times:', { startTime, endTime });
            
            if (!startTime || !endTime) {
                console.log('  Missing start or end time');
                warningDiv.style.display = 'none';
                return;
            }
            
            const duration = calculateDuration(startTime, endTime) / 60;
            console.log('  Duration in hours:', duration, 'courseHours:', courseHours);
            
            let warning = '';
            
            if (roomType === 'lecture') {
                const lecRemaining = lectureHours - courseHours.lecture;
                console.log('  Lecture validation: required=' + lectureHours + ', used=' + courseHours.lecture + ', remaining=' + lecRemaining + ', duration=' + duration);
                if (lecRemaining > 0 && duration > lecRemaining) {
                    warning = `This schedule would add ${duration}hrs of lecture, but only ${lecRemaining}hrs is remaining. Only ${lecRemaining}hrs is required for lecture.`;
                    console.log('  WARNING TRIGGERED:', warning);
                }
            } else if (roomType === 'laboratory') {
                const labRemaining = labHours - courseHours.lab;
                console.log('  Lab validation: required=' + labHours + ', used=' + courseHours.lab + ', remaining=' + labRemaining + ', duration=' + duration);
                if (labRemaining > 0 && duration > labRemaining) {
                    warning = `This schedule would add ${duration}hrs of lab, but only ${labRemaining}hrs is remaining. Only ${labRemaining}hrs is required for laboratory.`;
                    console.log('  WARNING TRIGGERED:', warning);
                }
            } else {
                console.log('  UNEXPECTED: roomType is neither lecture nor laboratory:', roomType);
            }
            
            if (warning) {
                document.getElementById('warning-text').textContent = warning;
                warningDiv.style.display = 'block';
            } else {
                warningDiv.style.display = 'none';
            }
        }

        // Validate course-room match for EDIT modal (excludes current schedule)
        function validateCourseRoomMatchEdit() {
            const courseSelect = document.getElementById('edit_course_select');
            const roomSelect = document.getElementById('edit_room_select');
            const warningDiv = document.getElementById('edit_course-warning');
            
            // Create the warning div if it doesn't exist
            if (!warningDiv) {
                const modal = document.getElementById('editScheduleModal');
                if (modal) {
                    const div = document.createElement('div');
                    div.id = 'edit_course-warning';
                    div.className = 'course-warning alert';
                    div.style.display = 'none';
                    div.innerHTML = '<strong>⚠️ Warning:</strong> <span id="edit_warning-text"></span>';
                    modal.insertBefore(div, modal.querySelector('.form-group'));
                }
            }
            
            const warningElement = document.getElementById('edit_course-warning');
            if (!warningElement) return; // Can't warn if div doesn't exist
            
            if (!courseSelect || !roomSelect || !courseSelect.value || !roomSelect.value) {
                warningElement.style.display = 'none';
                return;
            }
            
            const selectedOption = courseSelect.selectedOptions[0];
            const lectureHours = parseInt(selectedOption.dataset.lectureHours) || 0;
            const labHours = parseInt(selectedOption.dataset.laboratoryHours) || 0;
            
            const roomOption = roomSelect.selectedOptions[0];
            const roomType = roomOption.dataset.roomType;
            
            const sectionSelect = document.getElementById('section_select');
            const sectionId = sectionSelect ? sectionSelect.value : null;
            const courseId = courseSelect.value;
            
            if (!sectionId) {
                warningElement.style.display = 'none';
                return;
            }
            
            // Use the excluding function for edit mode to not count the current schedule
            const courseHours = getCourseHoursInSectionExcluding(courseId, sectionId, currentEditScheduleId);
            const startTime = document.getElementById('edit_start_time')?.value;
            const endTime = document.getElementById('edit_end_time')?.value;
            
            if (!startTime || !endTime) {
                warningElement.style.display = 'none';
                return;
            }
            
            const duration = calculateDuration(startTime, endTime) / 60;
            let warning = '';
            
            if (roomType === 'lecture') {
                const lecNewUsage = courseHours.lecture + duration;
                if (lectureHours > 0 && lecNewUsage > lectureHours) {
                    warning = `This would use ${lecNewUsage.toFixed(1)}hrs of lecture, but ${selectedOption.textContent.split(' - ')[0]} requires only ${lectureHours}hrs total.`;
                }
            } else if (roomType === 'laboratory') {
                const labNewUsage = courseHours.lab + duration;
                if (labHours > 0 && labNewUsage > labHours) {
                    warning = `This would use ${labNewUsage.toFixed(1)}hrs of lab, but ${selectedOption.textContent.split(' - ')[0]} requires only ${labHours}hrs total.`;
                }
            }
            
            if (warning) {
                document.getElementById('edit_warning-text').textContent = warning;
                warningElement.style.display = 'block';
            } else {
                warningElement.style.display = 'none';
            }
        }


        // Alert system
        function showAlert(message, type = 'info') {
            let container = document.querySelector('.alert-container');
            if (!container) {
                container = document.createElement('div');
                container.className = 'alert-container';
                document.body.appendChild(container);
            }
            
            const alert = document.createElement('div');
            alert.className = `alert ${type}`;
            
            const icons = {
                success: '<svg stroke="currentColor" viewBox="0 0 24 24" fill="none"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path></svg>',
                warning: '<svg stroke="currentColor" viewBox="0 0 24 24" fill="none"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path></svg>',
                error: '<svg stroke="currentColor" viewBox="0 0 24 24" fill="none"><path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path></svg>',
                info: '<svg stroke="currentColor" viewBox="0 0 24 24" fill="none"><path d="M13 16h-1v-4h1m0-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path></svg>'
            };
            
            alert.innerHTML = `${icons[type] || icons.info}<p class="alert-text">${message}</p>`;
            container.appendChild(alert);
            
            setTimeout(() => {
                alert.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => alert.remove(), 300);
            }, 5000);
            
            alert.addEventListener('click', () => {
                alert.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => alert.remove(), 300);
            });
        }

        // Loading overlay
        function showLoading() {
            document.getElementById('loadingOverlay').classList.add('show');
        }

        function hideLoading() {
            document.getElementById('loadingOverlay').classList.remove('show');
        }

        // Generate filters update
        function updateGenerateFilters() {
            // Placeholder - function removed with auto-generation feature
        }

        // CSRF helper
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        function fetchWithCSRF(url, options = {}) {
            if (!options.headers) options.headers = {};
            options.headers['X-CSRFToken'] = getCookie('csrftoken');
            return fetch(url, options);
        }

        // Manual schedule submission - IMPROVED with validation
        // Filter available days based on selected course and time conflicts
        function filterAvailableDays() {
            // Determine if we're in edit or add mode based on which elements exist
            const isEditMode = document.getElementById('edit_course_select')?.offsetParent !== null;
            
            let courseId, roomId, startTime, endTime, dayElements;
            
            if (isEditMode) {
                courseId = document.getElementById('edit_course_select').value;
                roomId = document.getElementById('edit_room_select').value;
                startTime = document.getElementById('edit_start_time')?.value;
                endTime = document.getElementById('edit_end_time')?.value;
                dayElements = document.querySelectorAll('#editScheduleModal select[name="day"] option');
            } else {
                courseId = document.getElementById('course_select').value;
                roomId = document.getElementById('room_select').value;
                startTime = document.getElementById('start_time')?.value;
                endTime = document.getElementById('end_time')?.value;
                dayElements = document.querySelectorAll('input[name="day"]');
            }
            
            const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const unavailableDays = new Set();
            
            console.log('DEBUG filterAvailableDays called (mode:', isEditMode ? 'edit' : 'add', ')');
            console.log('  courseId:', courseId);
            console.log('  roomId:', roomId);
            console.log('  time:', startTime, '-', endTime);
            console.log('  currentEditScheduleId:', currentEditScheduleId, '(type:', typeof currentEditScheduleId, ')');
            
            // Get the current schedule's day if in edit mode (to allow editing same day)
            const currentSchedule = isEditMode && currentEditScheduleId 
                ? currentSchedules.find(s => String(s.id) === String(currentEditScheduleId))
                : null;
            const currentScheduleDay = currentSchedule?.day;
            
            console.log('  currentSchedule:', currentSchedule);
            console.log('  currentScheduleDay:', currentScheduleDay);
            
            // Check for conflicts
            if (courseId && roomId && startTime && endTime) {
                const selectedCourseOption = isEditMode 
                    ? document.getElementById('edit_course_select').selectedOptions[0]
                    : document.getElementById('course_select').selectedOptions[0];
                const selectedCourseCode = selectedCourseOption?.textContent.split(' - ')[0] || '';
                console.log('  selectedCourseCode:', selectedCourseCode);
                
                currentSchedules.forEach((schedule, idx) => {
                    // Skip the current schedule being edited
                    if (isEditMode && String(schedule.id) === String(currentEditScheduleId)) {
                        console.log(`  Skipping current schedule (edit mode): ${schedule.id}`);
                        return;
                    }
                    
                    console.log(`  Checking schedule ${idx}:`, schedule);
                    
                    // Check 1: Duplicate course on same day
                    const scheduleCourseId = schedule.course_id ?? schedule.course?.id ?? schedule.course;
                    const sameCourse = scheduleCourseId != null
                        ? scheduleCourseId == courseId
                        : schedule.course_code && schedule.course_code === selectedCourseCode;
                    
                    // Check 2: Time conflict in same room
                    const scheduleRoomId = schedule.room_id ?? schedule.room?.id ?? schedule.room;
                    const sameRoom = scheduleRoomId == roomId;
                    const timeConflict = startTime && endTime && schedule.start_time && schedule.end_time 
                        ? timesOverlap(startTime, endTime, schedule.start_time, schedule.end_time)
                        : false;
                    
                    console.log(`    scheduleCourseId: ${scheduleCourseId}, sameCourse: ${sameCourse}`);
                    console.log(`    scheduleRoomId: ${scheduleRoomId}, sameRoom: ${sameRoom}, timeConflict: ${timeConflict}`);
                    
                    let dayIndex = parseInt(schedule.day);
                    if (Number.isNaN(dayIndex)) {
                        dayIndex = dayNames.indexOf(schedule.day);
                    }
                    
                    console.log(`    dayIndex: ${dayIndex}`);
                    
                    if (!Number.isNaN(dayIndex) && dayIndex >= 0) {
                        // Mark day as unavailable if:
                        // 1. Same course already scheduled, OR
                        // 2. Same room has a time conflict
                        if (sameCourse) {
                            console.log(`      -> UNAVAILABLE: Same course ${selectedCourseCode} already on ${dayNames[dayIndex]}`);
                            unavailableDays.add(dayIndex);
                        } else if (sameRoom && timeConflict) {
                            console.log(`      -> UNAVAILABLE: Room conflict on ${dayNames[dayIndex]}: ${startTime}-${endTime} overlaps with ${schedule.start_time}-${schedule.end_time}`);
                            unavailableDays.add(dayIndex);
                        }
                    }
                });
            }
            
            // In edit mode, the current day should ALWAYS remain available
            if (isEditMode && currentScheduleDay !== null && currentScheduleDay !== undefined) {
                unavailableDays.delete(parseInt(currentScheduleDay));
                console.log(`  Ensuring current day (${dayNames[currentScheduleDay]}) remains available for edit`);
            }
            
            console.log('DEBUG: unavailableDays =', Array.from(unavailableDays).map(d => dayNames[d]));
            
            // Update day selector visibility
            if (isEditMode) {
                // For edit mode, update select dropdown options
                const daySelect = document.getElementById('edit_day_select');
                if (daySelect) {
                    Array.from(daySelect.options).forEach((option, index) => {
                        if (index === 0) return; // Skip the "Select a day..." option
                        const dayNum = parseInt(option.value);
                        const isUnavailable = unavailableDays.has(dayNum);
                        option.disabled = isUnavailable;
                        option.style.color = isUnavailable ? '#ccc' : 'inherit';
                    });
                }
            } else {
                // For add mode, hide unavailable day checkboxes
                document.querySelectorAll('input[name="day"]').forEach(checkbox => {
                    const dayNum = parseInt(checkbox.value);
                    const isUnavailable = unavailableDays.has(dayNum);
                    
                    const label = checkbox.parentElement;
                    if (isUnavailable) {
                        label.style.display = 'none';
                        // Uncheck if it becomes hidden
                        if (checkbox.checked) {
                            checkbox.checked = false;
                        }
                    } else {
                        label.style.display = 'flex';
                    }
                });
                
                updateDayDropdownLabel();
            }
        }

        function getScheduleDayIndex(schedule) {
            const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            let dayIndex = parseInt(schedule.day);
            if (Number.isNaN(dayIndex)) {
                dayIndex = dayNames.indexOf(schedule.day);
            }
            return Number.isNaN(dayIndex) ? null : dayIndex;
        }

        function timeToMinutes(timeString) {
            if (!timeString) return null;
            const [hour, minute] = timeString.split(':').map(Number);
            if (Number.isNaN(hour) || Number.isNaN(minute)) return null;
            return hour * 60 + minute;
        }

        function timesOverlap(startA, endA, startB, endB) {
            const aStart = timeToMinutes(startA);
            const aEnd = timeToMinutes(endA);
            const bStart = timeToMinutes(startB);
            const bEnd = timeToMinutes(endB);
            if (aStart == null || aEnd == null || bStart == null || bEnd == null) return false;
            return aStart < bEnd && bStart < aEnd;
        }

        function fetchFacultySchedule(facultyId, excludeScheduleId = null) {
            const cacheKey = excludeScheduleId ? `${facultyId}_exclude_${excludeScheduleId}` : facultyId;
            if (facultyScheduleCache[cacheKey]) {
                return Promise.resolve(facultyScheduleCache[cacheKey]);
            }
            
            let url = `/admin/faculty/${facultyId}/schedule-data/`;
            if (excludeScheduleId) {
                url += `?exclude_schedule_id=${excludeScheduleId}`;
            }
            
            return fetch(url)
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        facultyScheduleCache[cacheKey] = data.schedules || [];
                        return facultyScheduleCache[cacheKey];
                    }
                    return [];
                })
                .catch(() => []);
        }

        async function filterAvailableInstructors(selectId = 'faculty_select') {
            const isEdit = selectId === 'edit_faculty_select';
            // For non-edit mode (batch creation with checkboxes), get first selected day
            let dayValue = null;
            if (!isEdit) {
                const selectedCheckboxes = document.querySelectorAll('input[name="day"]:checked');
                if (selectedCheckboxes.length > 0) {
                    dayValue = selectedCheckboxes[0].value;
                }
            } else {
                dayValue = document.getElementById('edit_day_select')?.value;
            }
            const startTime = document.getElementById(isEdit ? 'edit_start_time' : 'start_time')?.value;
            const endTime = document.getElementById(isEdit ? 'edit_end_time' : 'end_time')?.value;
            const facultySelect = document.getElementById(selectId);
            if (!facultySelect) return;

            // Get the schedule ID being edited (if any)
            const excludeScheduleId = isEdit ? document.getElementById('edit_schedule_id')?.value : null;

            const facultyIds = Array.from(facultySelect.querySelectorAll('option'))
                .map(option => option.value)
                .filter(value => value !== '');

            const unavailableFaculty = new Set();

            if (dayValue && startTime && endTime) {
                await Promise.all(facultyIds.map(async facultyId => {
                    const schedules = await fetchFacultySchedule(facultyId, excludeScheduleId);
                    schedules.forEach(schedule => {
                        const scheduleDay = getScheduleDayIndex(schedule);
                        if (scheduleDay === null || String(scheduleDay) !== dayValue) return;
                        if (!schedule.start_time || !schedule.end_time) return;
                        if (timesOverlap(startTime, endTime, schedule.start_time, schedule.end_time)) {
                            unavailableFaculty.add(String(facultyId));
                        }
                    });
                }));
            }

            facultySelect.querySelectorAll('option').forEach(option => {
                if (option.value === '') {
                    option.disabled = false;
                    option.hidden = false;
                    option.textContent = option.dataset.originalText || option.textContent;
                    return;
                }

                if (!option.dataset.originalText) {
                    option.dataset.originalText = option.textContent;
                }
                const originalText = option.dataset.originalText;
                const isConflict = unavailableFaculty.has(option.value);
                option.disabled = isConflict;
                option.hidden = isConflict;
                option.textContent = isConflict ? `${originalText} (Conflict)` : originalText;
            });

            const selectedOption = facultySelect.selectedOptions[0];
            if (selectedOption && selectedOption.disabled) {
                const name = selectedOption.dataset.originalText || selectedOption.textContent;
                showAlert(`${name} has a scheduling conflict with the selected day/time. Please choose another instructor.`, 'warning');
                facultySelect.value = '';
            }
        }

        // Validate that start time is before end time
        function validateTimeRange() {
            const startTimeInput = document.getElementById('start_time');
            const endTimeInput = document.getElementById('end_time');
            const startTime = startTimeInput.value;
            const endTime = endTimeInput.value;
            
            if (!startTime || !endTime) return true;
            
            if (startTime >= endTime) {
                showAlert('End time must be after start time', 'error');
                endTimeInput.focus();
                return false;
            }
            
            // Check time constraint (7:30 AM - 9:30 PM)
            if (startTime < '07:30' || startTime > '21:30') {
                showAlert('Start time must be between 7:30 AM and 9:30 PM', 'error');
                return false;
            }
            if (endTime < '07:30' || endTime > '21:30') {
                showAlert('End time must be between 7:30 AM and 9:30 PM', 'error');
                return false;
            }
            
            return true;
        }

        function initializeTimeWheels() {
            document.querySelectorAll('.time-wheel').forEach(wheel => {
                if (wheel.dataset.inited === 'true') return;
                const targetField = wheel.dataset.target;
                const input = document.getElementById(targetField);
                if (!input) return;

                const hourColumn = wheel.querySelector('.picker-column[data-unit="hour"]');
                const minuteColumn = wheel.querySelector('.picker-column[data-unit="minute"]');
                const periodColumn = wheel.querySelector('.picker-column[data-unit="period"]');
                if (!hourColumn || !minuteColumn || !periodColumn) return;

                buildInlineTimeColumn(hourColumn, Array.from({ length: 12 }, (_, index) => index + 1), 18);
                buildInlineTimeColumn(minuteColumn, Array.from({ length: 12 }, (_, index) => index * 5), 18);
                buildInlineTimeColumn(periodColumn, ['AM', 'PM'], 10, true);

                [hourColumn, minuteColumn, periodColumn].forEach(column => {
                    const unit = column.dataset.unit;
                    column.addEventListener('scroll', () => {
                        if (unit === 'period') {
                            updateInlineSelectionFromScroll(column);
                        } else {
                            handleInfiniteScroll(column, unit);
                        }
                        updateInlineTimeValueFromWheel(wheel);
                        scheduleCenterAfterScroll(column);
                    });
                });

                wheel.dataset.inited = 'true';
                syncInlineTimeWheel(wheel, true);
            });
        }

        function buildInlineTimeColumn(column, values, repeatCount, isText = false) {
            column.innerHTML = '';
            for (let i = 0; i < 4; i++) {
                appendInlineSpacer(column);
            }
            for (let repeat = 0; repeat < repeatCount; repeat++) {
                values.forEach(value => {
                    const item = document.createElement('button');
                    item.type = 'button';
                    item.className = 'picker-item';
                    item.dataset.value = value;
                    item.textContent = isText ? value : value.toString().padStart(2, '0');
                    item.addEventListener('click', () => selectInlineTimeItem(column, value));
                    column.appendChild(item);
                });
            }
            for (let i = 0; i < 4; i++) {
                appendInlineSpacer(column);
            }
        }

        function appendInlineSpacer(column) {
            const spacer = document.createElement('div');
            spacer.className = 'picker-item time-picker-spacer';
            spacer.innerHTML = '&nbsp;';
            column.appendChild(spacer);
        }

        function selectInlineTimeItem(column, value) {
            const unit = column.dataset.unit;
            scrollInlineColumnToValue(column, value, true);
            updateInlineSelectionFromScroll(column);
            const wheel = column.closest('.time-wheel');
            if (wheel) updateInlineTimeValueFromWheel(wheel);
        }

        function scrollInlineColumnToValue(column, value, instant = false) {
            const items = Array.from(column.querySelectorAll('.picker-item'));
            const matching = items.filter(item => !item.classList.contains('time-picker-spacer') &&
                (column.dataset.unit === 'period'
                    ? item.dataset.value === value
                    : parseInt(item.dataset.value) === value));
            if (!matching.length) return;

            let closest = matching[0];
            let minDist = Infinity;
            const center = column.getBoundingClientRect().top + column.clientHeight / 2;
            matching.forEach(item => {
                const rect = item.getBoundingClientRect();
                const mid = rect.top + rect.height / 2;
                const dist = Math.abs(center - mid);
                if (dist < minDist) {
                    minDist = dist;
                    closest = item;
                }
            });

            closest.scrollIntoView({
                behavior: instant ? 'auto' : 'smooth',
                block: 'center'
            });
            updateInlineSelectionVisual(column, value);
        }

        function updateInlineSelectionFromScroll(column) {
            const items = Array.from(column.querySelectorAll('.picker-item:not(.time-picker-spacer)'));
            const center = column.getBoundingClientRect().top + column.clientHeight / 2;

            let closest = null;
            let minDist = Infinity;
            items.forEach(item => {
                const rect = item.getBoundingClientRect();
                const mid = rect.top + rect.height / 2;
                const dist = Math.abs(center - mid);
                if (dist < minDist) {
                    minDist = dist;
                    closest = item;
                }
            });

            if (!closest) return;
            items.forEach(item => item.classList.remove('selected'));
            closest.classList.add('selected');
        }

        function updateInlineSelectionVisual(column, value) {
            const items = Array.from(column.querySelectorAll('.picker-item:not(.time-picker-spacer)'));
            items.forEach(item => item.classList.remove('selected'));

            const matching = items.filter(item =>
                column.dataset.unit === 'period'
                    ? item.dataset.value === value
                    : parseInt(item.dataset.value) === value);
            if (!matching.length) return;

            let closest = matching[0];
            let minDist = Infinity;
            const center = column.getBoundingClientRect().top + column.clientHeight / 2;
            matching.forEach(item => {
                const rect = item.getBoundingClientRect();
                const mid = rect.top + rect.height / 2;
                const dist = Math.abs(center - mid);
                if (dist < minDist) {
                    minDist = dist;
                    closest = item;
                }
            });
            closest.classList.add('selected');
        }

        function getInlineSelectedValue(column) {
            const selected = column.querySelector('.picker-item.selected');
            if (selected) {
                return column.dataset.unit === 'period' ? selected.dataset.value : parseInt(selected.dataset.value);
            }
            const items = Array.from(column.querySelectorAll('.picker-item:not(.time-picker-spacer)'));
            const center = column.getBoundingClientRect().top + column.clientHeight / 2;
            let closest = null;
            let minDist = Infinity;
            items.forEach(item => {
                const rect = item.getBoundingClientRect();
                const mid = rect.top + rect.height / 2;
                const dist = Math.abs(center - mid);
                if (dist < minDist) {
                    minDist = dist;
                    closest = item;
                }
            });
            if (!closest) return null;
            return column.dataset.unit === 'period' ? closest.dataset.value : parseInt(closest.dataset.value);
        }

        function syncInlineTimeWheelForTarget(fieldId) {
            const wheel = document.querySelector(`.time-wheel[data-target="${fieldId}"]`);
            if (!wheel) return;
            if (wheel.dataset.inited !== 'true') initializeTimeWheels();
            syncInlineTimeWheel(wheel, true);
        }

        function syncInlineTimeWheel(wheel, instant = false) {
            const targetField = wheel.dataset.target;
            const input = document.getElementById(targetField);
            if (!input) return;

            const [time12, period] = convertTo12Hour(input.value || '07:30');
            const [hourString, minuteString] = time12.split(':');
            const hour = parseInt(hourString, 10);
            const minute = parseInt(minuteString, 10);

            const hourColumn = wheel.querySelector('.picker-column[data-unit="hour"]');
            const minuteColumn = wheel.querySelector('.picker-column[data-unit="minute"]');
            const periodColumn = wheel.querySelector('.picker-column[data-unit="period"]');
            if (!hourColumn || !minuteColumn || !periodColumn) return;

            scrollInlineColumnToValue(hourColumn, hour, instant);
            scrollInlineColumnToValue(minuteColumn, minute, instant);
            scrollInlineColumnToValue(periodColumn, period, instant);

            updateInlineSelectionVisual(hourColumn, hour);
            updateInlineSelectionVisual(minuteColumn, minute);
            updateInlineSelectionVisual(periodColumn, period);
            updateInlineTimeValueFromWheel(wheel);
        }

        function updateInlineTimeValueFromWheel(wheel) {
            const hourColumn = wheel.querySelector('.picker-column[data-unit="hour"]');
            const minuteColumn = wheel.querySelector('.picker-column[data-unit="minute"]');
            const periodColumn = wheel.querySelector('.picker-column[data-unit="period"]');
            const input = document.getElementById(wheel.dataset.target);
            if (!hourColumn || !minuteColumn || !periodColumn || !input) return;

            const hour = getInlineSelectedValue(hourColumn);
            const minute = getInlineSelectedValue(minuteColumn);
            const period = getInlineSelectedValue(periodColumn);
            if (hour == null || minute == null || !period) return;

            input.value = convertTo24Hour(hour, minute, period);
            if (wheel.dataset.target === 'start_time' || wheel.dataset.target === 'end_time') {
                updateDurationDisplay();
            } else if (wheel.dataset.target === 'edit_start_time' || wheel.dataset.target === 'edit_end_time') {
                updateDurationDisplayEdit();
            }
        }

        document.addEventListener('DOMContentLoaded', initializeTimeWheels);

        // Update duration display
        function updateDurationDisplay() {
            const startTime = document.getElementById('start_time').value;
            const endTime = document.getElementById('end_time').value;
            
            if (!startTime || !endTime) {
                document.getElementById('duration-display').style.display = 'none';
                document.getElementById('course-warning').style.display = 'none';
                return;
            }
            
            if (startTime >= endTime) {
                document.getElementById('duration-display').style.display = 'none';
                document.getElementById('course-warning').style.display = 'none';
                return;
            }
            
            // Calculate duration
            const [startHour, startMin] = startTime.split(':').map(Number);
            const [endHour, endMin] = endTime.split(':').map(Number);
            const durationMinutes = (endHour * 60 + endMin) - (startHour * 60 + startMin);
            
            let durationText = '';
            if (durationMinutes < 60) {
                durationText = `${durationMinutes} minutes`;
            } else {
                const hours = Math.floor(durationMinutes / 60);
                const mins = durationMinutes % 60;
                if (mins === 0) {
                    durationText = `${hours} hour${hours > 1 ? 's' : ''}`;
                } else {
                    durationText = `${hours} hour${hours > 1 ? 's' : ''} ${mins} minutes`;
                }
            }
            
            document.getElementById('duration-text').textContent = durationText;
            document.getElementById('duration-display').style.display = 'block';
            
            // Validate course-room match when time changes
            validateCourseRoomMatch();
        }

        // Update duration display for EDIT modal
        function updateDurationDisplayEdit() {
            const startTime = document.getElementById('edit_start_time').value;
            const endTime = document.getElementById('edit_end_time').value;
            
            if (!startTime || !endTime) {
                document.getElementById('duration-display-edit').style.display = 'none';
                const warningDiv = document.getElementById('edit_course-warning');
                if (warningDiv) warningDiv.style.display = 'none';
                return;
            }
            
            if (startTime >= endTime) {
                document.getElementById('duration-display-edit').style.display = 'none';
                const warningDiv = document.getElementById('edit_course-warning');
                if (warningDiv) warningDiv.style.display = 'none';
                return;
            }
            
            // Calculate duration
            const [startHour, startMin] = startTime.split(':').map(Number);
            const [endHour, endMin] = endTime.split(':').map(Number);
            const durationMinutes = (endHour * 60 + endMin) - (startHour * 60 + startMin);
            
            let durationText = '';
            if (durationMinutes < 60) {
                durationText = `${durationMinutes} minutes`;
            } else {
                const hours = Math.floor(durationMinutes / 60);
                const mins = durationMinutes % 60;
                if (mins === 0) {
                    durationText = `${hours} hour${hours > 1 ? 's' : ''}`;
                } else {
                    durationText = `${hours} hour${hours > 1 ? 's' : ''} ${mins} minutes`;
                }
            }
            
            document.getElementById('duration-text-edit').textContent = durationText;
            document.getElementById('duration-display-edit').style.display = 'block';
            
            // Validate course-room match when time changes in edit modal
            validateCourseRoomMatchEdit();
        }

        function submitCreateSchedule(event) {
            event.preventDefault();
            
            // Validate times before submitting
            if (!validateTimeRange()) {
                return;
            }
            
            // Get all selected days from checkboxes
            const dayCheckboxes = document.querySelectorAll('input[name="day"]:checked');
            const selectedDays = Array.from(dayCheckboxes).map(cb => parseInt(cb.value));
            
            // Validate at least one day is selected
            if (selectedDays.length === 0) {
                showAlert('Please select at least one day.', 'error');
                return;
            }
            
            const courseId = document.getElementById('course_select').value;
            const courseOption = document.getElementById('course_select').options[document.getElementById('course_select').selectedIndex];
            const courseCode = courseOption.textContent.split(' - ')[0]; // Extract course code
            const courseSelect = document.getElementById('course_select');
            const roomSelect = document.getElementById('room_select');
            const sectionSelect = document.getElementById('section_select');
            
            // DEBUG: Log selected days
            console.log('DEBUG submitCreateSchedule: selectedDays =', selectedDays);
            
            // Validate all days before creating any schedules
            for (const dayValue of selectedDays) {
                // Check for duplicate course on same day
                if (courseId && dayValue !== null && dayValue !== undefined) {
                    const isDuplicate = currentSchedules.some(schedule => 
                        schedule.course_id == courseId && schedule.day == dayValue
                    );
                    
                    if (isDuplicate) {
                        const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
                        showAlert(`${courseCode} is already scheduled on ${dayNames[dayValue]}. A course cannot have multiple sessions on the same day.`, 'error');
                        return;
                    }
                }
                
                // Check if schedule would exceed required hours
                if (courseSelect.value && roomSelect.value && sectionSelect.value) {
                    const selectedCourseOption = courseSelect.selectedOptions[0];
                    const lectureHours = parseInt(selectedCourseOption.dataset.lectureHours) || 0;
                    const labHours = parseInt(selectedCourseOption.dataset.laboratoryHours) || 0;
                    
                    const roomOption = roomSelect.selectedOptions[0];
                    const roomType = roomOption.dataset.roomType;
                    
                    const sectionId = sectionSelect.value;
                    const courseHours = getCourseHoursInSection(courseId, sectionId);
                    
                    const startTime = document.getElementById('start_time')?.value;
                    const endTime = document.getElementById('end_time')?.value;
                    
                    if (startTime && endTime) {
                        const duration = calculateDuration(startTime, endTime) / 60; // convert to hours
                        
                        // Check if this schedule would exceed requirements
                        if (roomType === 'lecture') {
                            const lecRemaining = lectureHours - courseHours.lecture;
                            if (lectureHours > 0 && lecRemaining <= 0) {
                                showAlert(`Cannot add schedule: ${courseCode} already has all required lecture hours (${lectureHours} hrs).`, 'error');
                                return;
                            }
                            if (lectureHours > 0 && duration > lecRemaining) {
                                showAlert(`Cannot add schedule: This would add ${duration}hrs of lecture, but only ${lecRemaining}hrs is remaining. ${courseCode} requires ${lectureHours}hrs total.`, 'error');
                                return;
                            }
                        } else if (roomType === 'laboratory') {
                            const labRemaining = labHours - courseHours.lab;
                            if (labHours > 0 && labRemaining <= 0) {
                                showAlert(`Cannot add schedule: ${courseCode} already has all required lab hours (${labHours} hrs).`, 'error');
                                return;
                            }
                            if (labHours > 0 && duration > labRemaining) {
                                showAlert(`Cannot add schedule: This would add ${duration}hrs of lab, but only ${labRemaining}hrs is remaining. ${courseCode} requires ${labHours}hrs total.`, 'error');
                                return;
                            }
                        }
                    }
                }
            }
            
            // All validations passed, now create schedules for each day
            const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const results = { success: [], failed: [] };
            
            // Create a counter to track completion
            let completedRequests = 0;
            
            for (const dayValue of selectedDays) {
                const formData = new FormData();
                
                // Copy all form data except the day
                const originalForm = event.target;
                for (const [key, value] of new FormData(originalForm)) {
                    if (key !== 'day') {
                        formData.append(key, value);
                    }
                }
                
                // Add the specific day for this iteration
                formData.append('day', dayValue);
                
                fetchWithCSRF('/admin/schedule/add/', {
                    method: 'POST',
                    body: formData
                })
                .then(res => res.json())
                .then(data => {
                    completedRequests++;
                    
                    if (data.success) {
                        results.success.push(dayNames[dayValue]);
                    } else {
                        // Get detailed error message
                        let errorMsg = 'Unknown error';
                        if (data.error) {
                            errorMsg = data.error;
                        } else if (data.errors) {
                            errorMsg = Array.isArray(data.errors) ? data.errors.join(', ') : data.errors;
                        }
                        
                        console.error(`Create error for ${dayNames[dayValue]}:`, data);
                        results.failed.push({
                            day: dayNames[dayValue],
                            error: errorMsg
                        });
                    }
                    
                    // Check if all requests completed
                    if (completedRequests === selectedDays.length) {
                        handleBatchScheduleResults(results, courseCode);
                    }
                })
                .catch(err => {
                    completedRequests++;
                    console.error(`Create error for ${dayNames[dayValue]}:`, err);
                    results.failed.push({
                        day: dayNames[dayValue],
                        error: err.message || 'Network error'
                    });
                    
                    if (completedRequests === selectedDays.length) {
                        handleBatchScheduleResults(results, courseCode);
                    }
                });
            }
        }
        
        // Handle batch schedule creation results
        function handleBatchScheduleResults(results, courseCode) {
            const successCount = results.success.length;
            const failureCount = results.failed.length;
            
            console.log('DEBUG handleBatchScheduleResults: results =', results);
            
            if (successCount > 0 && failureCount === 0) {
                // All succeeded
                const daysText = results.success.join(', ');
                showAlert(`Schedule created successfully for ${courseCode} on ${daysText}!`, 'success');
                closeModal('scheduleModal');
                
                if (currentSectionId) {
                    setTimeout(() => {
                        const sectionName = document.getElementById('scheduleSectionName').textContent;
                        const curriculum = document.getElementById('scheduleCurriculum').textContent;
                        loadScheduleView(currentSectionId, sectionName, curriculum);
                    }, 500);
                } else {
                    setTimeout(() => window.location.reload(), 800);
                }
            } else if (successCount > 0 && failureCount > 0) {
                // Partial success
                let message = `Schedule created for ${courseCode} on ${results.success.join(', ')}.\n\nFailed days:\n`;
                results.failed.forEach(f => {
                    message += `• ${f.day}: ${f.error}\n`;
                });
                showAlert(message, 'warning');
                
                // Reload after a delay to show partial success
                if (currentSectionId) {
                    setTimeout(() => {
                        const sectionName = document.getElementById('scheduleSectionName').textContent;
                        const curriculum = document.getElementById('scheduleCurriculum').textContent;
                        loadScheduleView(currentSectionId, sectionName, curriculum);
                    }, 500);
                } else {
                    setTimeout(() => window.location.reload(), 800);
                }
            } else {
                // All failed
                let message = `Failed to create schedule for ${courseCode}:\n`;
                results.failed.forEach(f => {
                    message += `• ${f.day}: ${f.error}\n`;
                });
                showAlert(message, 'error');
            }
        }

        // Edit schedule functions
        function openAddScheduleModal(sectionId) {
            currentEditScheduleId = null;  // Mark as add mode
            
            fetch(`/admin/schedule/edit/new/?section=${sectionId}`)
                .then(res => res.json())
                .then(data => {
                    // Reset form for new schedule
                    document.getElementById('edit_schedule_id').value = '';
                    document.getElementById('edit_section_id').value = sectionId;
                    document.getElementById('edit_section_display').value = document.getElementById('scheduleSectionName').textContent;
                    document.getElementById('edit_course_select').value = '';
                    document.getElementById('edit_faculty_select').value = '';
                    document.getElementById('edit_room_select').value = '';
                    document.getElementById('edit_day_select').value = '';
                    
                    document.getElementById('edit_start_time').value = '07:30';
                    document.getElementById('edit_end_time').value = '08:30';
                    setTimeDisplay('edit_start_time');
                    setTimeDisplay('edit_end_time');
                    
                    // Hide the delete button for new schedules
                    const deleteBtn = document.querySelector('.btn-delete');
                    if (deleteBtn) {
                        deleteBtn.style.display = 'none';
                    }
                    
                    // Update modal title and button text
                    document.querySelector('#editScheduleModal .modal-header h2').textContent = 'Add New Schedule';
                    const submitBtn = document.querySelector('#editScheduleForm button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.textContent = 'Create Schedule';
                    }
                    
                    // Hide duration display for new schedule
                    const durationDisplay = document.getElementById('duration-display-edit');
                    if (durationDisplay) {
                        durationDisplay.style.display = 'none';
                    }
                    
                    openModal('editScheduleModal');
                })
                .catch(err => {
                    console.error('Error opening add schedule modal:', err);
                    showAlert('Error opening schedule form', 'error');
                });
        }

        function openEditScheduleModal(scheduleId) {
            currentEditScheduleId = scheduleId;
            
            fetch(`/admin/schedule/edit/${scheduleId}/`)
                .then(res => res.json())
                .then(data => {
                    document.getElementById('edit_schedule_id').value = data.id;
                    document.getElementById('edit_section_id').value = data.section;
                    document.getElementById('edit_section_display').value = document.querySelector(`option[value="${data.section}"]`)?.textContent || '';
                    document.getElementById('edit_course_select').value = data.course;
                    document.getElementById('edit_faculty_select').value = data.faculty;
                    document.getElementById('edit_room_select').value = data.room;
                    document.getElementById('edit_day_select').value = data.day;
                    
                    document.getElementById('edit_start_time').value = data.start_time;
                    document.getElementById('edit_end_time').value = data.end_time;
                    setTimeDisplay('edit_start_time');
                    setTimeDisplay('edit_end_time');
                    filterAvailableInstructors('edit_faculty_select');
                    filterAvailableDays(); // Filter days based on course and room constraints
                    showCourseRequirements('edit'); // Show course requirements info
                    
                    // Show the delete button for existing schedules
                    const deleteBtn = document.querySelector('.btn-delete');
                    if (deleteBtn) {
                        deleteBtn.style.display = 'inline-flex';
                    }
                    
                    // Update modal title and button text
                    document.querySelector('#editScheduleModal .modal-header h2').textContent = 'Edit Schedule';
                    const submitBtn = document.querySelector('#editScheduleForm button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.textContent = 'Update Schedule';
                    }
                    
                    // Update duration display for edit modal
                    const [startHour, startMin] = data.start_time.split(':').map(Number);
                    const [endHour, endMin] = data.end_time.split(':').map(Number);
                    const durationMinutes = (endHour * 60 + endMin) - (startHour * 60 + startMin);
                    
                    let durationText = '';
                    if (durationMinutes < 60) {
                        durationText = `${durationMinutes} minutes`;
                    } else {
                        const hours = Math.floor(durationMinutes / 60);
                        const mins = durationMinutes % 60;
                        if (mins === 0) {
                            durationText = `${hours} hour${hours > 1 ? 's' : ''}`;
                        } else {
                            durationText = `${hours} hour${hours > 1 ? 's' : ''} ${mins} minutes`;
                        }
                    }
                    
                    document.getElementById('duration-text-edit').textContent = durationText;
                    document.getElementById('duration-display-edit').style.display = 'block';
                    
                    openModal('editScheduleModal');
                })
                .catch(err => {
                    console.error('Error loading schedule:', err);
                    showAlert('Error loading schedule data', 'error');
                });
        }

        function submitEditSchedule(event) {
            event.preventDefault();
            
            // Validate times before submitting
            const startTimeEdit = document.getElementById('edit_start_time').value;
            const endTimeEdit = document.getElementById('edit_end_time').value;
            
            if (!startTimeEdit || !endTimeEdit) {
                showAlert('Please select both start and end times', 'error');
                return;
            }
            
            if (startTimeEdit >= endTimeEdit) {
                showAlert('End time must be after start time', 'error');
                return;
            }
            
            if (startTimeEdit < '07:30' || startTimeEdit > '21:30') {
                showAlert('Start time must be between 7:30 AM and 9:30 PM', 'error');
                return;
            }
            if (endTimeEdit < '07:30' || endTimeEdit > '21:30') {
                showAlert('End time must be between 7:30 AM and 9:30 PM', 'error');
                return;
            }
            
            // Determine if this is add or edit mode
            const isAdd = !currentEditScheduleId;
            
            // FIXED VALIDATION: Check if editing/adding would exceed required hours
            // Exclude the current schedule being edited from the calculation (null for add mode)
            const courseSelect = document.getElementById('edit_course_select');
            const roomSelect = document.getElementById('edit_room_select');
            const sectionSelect = isAdd ? document.getElementById('edit_section_id') : document.getElementById('section_select');
            
            // Validate course and section are selected (room is optional)
            if (courseSelect.value && sectionSelect.value) {
                const selectedCourseOption = courseSelect.selectedOptions[0];
                const lectureHours = parseInt(selectedCourseOption.dataset.lectureHours) || 0;
                const labHours = parseInt(selectedCourseOption.dataset.laboratoryHours) || 0;
                const courseId = courseSelect.value;
                
                const roomOption = roomSelect.value ? roomSelect.selectedOptions[0] : null;
                const roomType = roomOption ? roomOption.dataset.roomType : null;
                
                const sectionId = sectionSelect.value;
                const newDuration = calculateDuration(startTimeEdit, endTimeEdit) / 60; // convert to hours
                
                // Get hours excluding THIS schedule being edited (or all for new schedules)
                const courseHoursExcluding = getCourseHoursInSectionExcluding(courseId, sectionId, currentEditScheduleId);
                
                // Check if this edit/add would exceed requirements
                if (roomType === 'lecture') {
                    const lecNewUsage = courseHoursExcluding.lecture + newDuration;
                    
                    if (lectureHours > 0 && lecNewUsage > lectureHours) {
                        const courseCode = selectedCourseOption.textContent.split(' - ')[0];
                        showAlert(`Cannot ${isAdd ? 'create' : 'update'}: This would use ${lecNewUsage.toFixed(1)}hrs of lecture, but ${courseCode} requires only ${lectureHours}hrs total.`, 'error');
                        return;
                    }
                } else if (roomType === 'laboratory') {
                    const labNewUsage = courseHoursExcluding.lab + newDuration;
                    
                    if (labHours > 0 && labNewUsage > labHours) {
                        const courseCode = selectedCourseOption.textContent.split(' - ')[0];
                        showAlert(`Cannot ${isAdd ? 'create' : 'update'}: This would use ${labNewUsage.toFixed(1)}hrs of lab, but ${courseCode} requires only ${labHours}hrs total.`, 'error');
                        return;
                    }
                } else if (!roomType) {
                    // No room selected or room has no type - assume lecture by default
                    const lecNewUsage = courseHoursExcluding.lecture + newDuration;
                    
                    if (lectureHours > 0 && lecNewUsage > lectureHours) {
                        const courseCode = selectedCourseOption.textContent.split(' - ')[0];
                        showAlert(`Cannot ${isAdd ? 'create' : 'update'}: This would use ${lecNewUsage.toFixed(1)}hrs of lecture, but ${courseCode} requires only ${lectureHours}hrs total.`, 'error');
                        return;
                    }
                }
            }
            
            const formData = new FormData(event.target);
            const scheduleId = document.getElementById('edit_schedule_id').value;
            
            // Determine the endpoint based on add/edit mode
            const endpoint = isAdd ? '/admin/schedule/edit/new/' : `/admin/schedule/edit/${scheduleId}/`;
            
            // For add mode, ensure section is in the form data
            if (isAdd && !formData.has('section')) {
                formData.set('section', document.getElementById('edit_section_id').value);
            }
            
            fetchWithCSRF(endpoint, {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showAlert(isAdd ? 'Schedule created successfully!' : 'Schedule updated successfully!', 'success');
                    closeModal('editScheduleModal');
                    if (currentSectionId) {
                        setTimeout(() => {
                            const sectionName = document.getElementById('scheduleSectionName').textContent;
                            const curriculum = document.getElementById('scheduleCurriculum').textContent;
                            loadScheduleView(currentSectionId, sectionName, curriculum);
                        }, 500);
                    }
                } else {
                    const err = data.errors ? data.errors.join(', ') : (data.error || 'Unknown error');
                    showAlert(`Error ${isAdd ? 'creating' : 'updating'} schedule: ` + err, 'error');
                }
            })
            .catch(err => {
                console.error('Schedule action error:', err);
                showAlert(`Error ${isAdd ? 'creating' : 'updating'} schedule`, 'error');
            });
        }

        function deleteScheduleFromEdit() {
            const scheduleId = document.getElementById('edit_schedule_id').value;
            
            if (!confirm('Are you sure you want to delete this schedule?')) {
                return;
            }
            
            fetchWithCSRF(`/admin/schedule/delete/${scheduleId}/`, {
                method: 'POST'
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showAlert('Schedule deleted successfully!', 'success');
                    closeModal('editScheduleModal');
                    if (currentSectionId) {
                        setTimeout(() => {
                            const sectionName = document.getElementById('scheduleSectionName').textContent;
                            const curriculum = document.getElementById('scheduleCurriculum').textContent;
                            loadScheduleView(currentSectionId, sectionName, curriculum);
                        }, 500);
                    }
                } else {
                    showAlert('Error deleting schedule', 'error');
                }
            })
            .catch(err => {
                console.error('Delete error:', err);
                showAlert('Error deleting schedule', 'error');
            });
        }

        // Load schedule view
        function loadScheduleView(sectionId, sectionName, curriculum) {
            currentSectionId = sectionId;
            
            document.getElementById('scheduleSectionName').textContent = sectionName;
            document.getElementById('scheduleCurriculum').textContent = curriculum;
            document.getElementById('sidebarCurriculum').textContent = curriculum;
            
            document.getElementById('scheduleEmptyState').style.display = 'none';
            // Use block to match Section page rendering
            document.getElementById('scheduleView').style.display = 'block';
            
            document.querySelectorAll('.section-card').forEach(card => card.classList.remove('selected'));
            const cardEl = document.querySelector(`.section-card[data-section-id="${sectionId}"]`);
            if (cardEl) cardEl.classList.add('selected');
            
            console.log('DEBUG loadScheduleView:', { sectionId, sectionName });
            
            fetch(`/admin/section/${sectionId}/schedule-data/`)
                .then(res => res.json())
                .then(data => {
                    console.log('DEBUG API response:', data);
                    if (data.success) {
                        currentSchedules = data.schedules; // Store schedules for duplicate check
                        console.log('  Stored currentSchedules:', currentSchedules);
                        renderScheduleGrid(data.schedules);
                        renderCoursesSidebar(data.courses);
                        filterAvailableInstructors('faculty_select');
                    } else {
                        console.error('Error loading schedule:', data.error);
                        showAlert('Error loading schedule data', 'error');
                    }
                })
                .catch(err => {
                    console.error('Error loading schedule view:', err);
                    showAlert('Error loading schedule', 'error');
                });
        }

        // Render schedule grid
        function renderScheduleGrid(schedules) {
            const timeColumn = document.getElementById('timeColumn');
            timeColumn.innerHTML = '';

            // Use the same time slot generation as Section page
            const timeSlots = generateTimeSlots();

            // Add time labels at proper positions
            timeSlots.forEach(time => {
                const label = document.createElement('div');
                label.className = 'time-label';
                label.textContent = formatTimeLabel(time);
                label.style.top = `${calculateTopPosition(time)}px`;
                timeColumn.appendChild(label);
            });

            // Clear all day columns
            document.querySelectorAll('.schedule-day-column').forEach(col => {
                col.innerHTML = '';
            });

            // Render schedule blocks
            schedules.forEach(schedule => {
                    // Allow flexible day formats from server (0-5, 1-6, or weekday names)
                    const dayColumn = findDayColumn(schedule.day);
                if (!dayColumn) return;

                const block = document.createElement('div');
                block.className = 'schedule-block';
                // attach schedule id so handlers can reference it
                block.dataset.scheduleId = schedule.id;

                // Calculate position and height
                const topPos = calculateTopPosition(schedule.start_time);
                const duration = schedule.duration || calculateDuration(schedule.start_time, schedule.end_time);
                const height = (duration / 30) * 60; // 60px per 30 minutes

                // Apply styles
                const hexColor = schedule.course_color;
                block.style.backgroundColor = hexToRGBA(hexColor, 0.25);
                block.style.borderLeftColor = hexColor;
                block.style.top = `${topPos}px`;
                block.style.height = `${height}px`;

                // Add content (match Section page)
                block.innerHTML = `
                    <div class="schedule-course-code">${schedule.course_code}</div>
                    <div class="schedule-details">${formatTimeLabel(schedule.start_time)} - ${formatTimeLabel(schedule.end_time)}</div>
                    <div class="schedule-details">Room: ${schedule.room || 'TBA'}</div>
                    <div class="schedule-details">Section: ${schedule.section_name || ''}</div>
                    <div class="schedule-details">Professor: ${schedule.faculty || 'TBA'}</div>
                `;

                // debugging: log each schedule rendered to the browser console
                try {
                    console.debug('renderScheduleGrid item', schedule.id, schedule.course_code, 'day', schedule.day, schedule.start_time + '-' + schedule.end_time, 'top', topPos, 'height', height);
                } catch (e) {
                    // ignore if console not available
                }

                // clicking a block should open the edit modal (delete/edit from there)
                block.addEventListener('click', (e) => {
                    e.stopPropagation();
                    openEditScheduleModal(schedule.id);
                });

                dayColumn.appendChild(block);
            });
        }

        function calculateTopPosition(timeStr) {
            const [hours, minutes] = timeStr.split(':').map(Number);
                // Grid starts at 07:00 so subtract 7*60 = 420 minutes
                const gridStart = 7 * 60;
            const totalMinutes = (hours * 60 + minutes) - gridStart;
            return (totalMinutes / 30) * 60;
        }

        // Normalize/resolve different day formats coming from server
        function findDayColumn(dayValue) {
            // If already a column element was passed accidentally, return it
            if (dayValue instanceof Element && dayValue.classList.contains('schedule-day-column')) return dayValue;

            let idx = null;

            // numeric-like values
            if (typeof dayValue === 'number' || (/^\d+$/.test(String(dayValue)))) {
                const n = parseInt(dayValue, 10);
                // If server sends 0..5 (our template) use directly
                if (n >= 0 && n <= 5) idx = n;
                // If server uses 1..6 (Mon=1..Sat=6) convert to 0..5
                else if (n >= 1 && n <= 6) idx = n - 1;
                // If it's 7 or larger, map 7->6 (Sunday) but we don't have Sunday column -> return null
                else idx = null;
            } else if (typeof dayValue === 'string') {
                const s = dayValue.trim().toLowerCase();
                const nameMap = { monday: 0, tuesday: 1, wednesday: 2, thursday: 3, friday: 4, saturday: 5 };
                if (nameMap.hasOwnProperty(s)) idx = nameMap[s];
                else if (/^\d+$/.test(s)) {
                    const n = parseInt(s, 10);
                    if (n >= 0 && n <= 5) idx = n;
                    else if (n >= 1 && n <= 6) idx = n - 1;
                }
            }

            if (idx === null) {
                // no matching column
                console.warn('Unrecognized schedule.day value:', dayValue);
                return null;
            }

            return document.querySelector(`.schedule-day-column[data-day="${idx}"]`);
        }

        function hexToRGBA(hex, alpha) {
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }

        function calculateDuration(startTime, endTime) {
            const [startHour, startMin] = startTime.split(':').map(Number);
            const [endHour, endMin] = endTime.split(':').map(Number);
            return (endHour * 60 + endMin) - (startHour * 60 + startMin);
        }

        function renderCoursesSidebar(courses) {
            const coursesList = document.getElementById('coursesList');
            coursesList.innerHTML = '';
            
            if (!courses || courses.length === 0) {
                coursesList.innerHTML = '<div class="card-empty-message">No courses available</div>';
                return;
            }
            
            courses.forEach(course => {
                const courseItem = document.createElement('div');
                courseItem.className = 'course-item';
                courseItem.style.borderLeftColor = course.color;
                courseItem.innerHTML = `
                    <div class="course-details">
                        <div class="course-code">${course.course_code}</div>
                        <div class="course-title">${course.descriptive_title}</div>
                        <div class="course-info">
                            <span>Lecture: ${course.lecture_hours}h</span>
                            <span>Laboratory: ${course.laboratory_hours}h</span>
                            <span>Credit Unit: ${course.credit_units}</span>
                        </div>
                    </div>
                `;
                coursesList.appendChild(courseItem);
            });
        }

        function generateTimeSlots() {
            const slots = [];
            // Start at 7:30 AM
            slots.push('07:30');
            // 8:00 to 9:00 PM (21:00)
            for (let hour = 8; hour <= 21; hour++) {
                slots.push(`${hour.toString().padStart(2, '0')}:00`);
                if (hour < 21) {
                    slots.push(`${hour.toString().padStart(2, '0')}:30`);
                }
            }
            // End at 9:30 PM
            slots.push('21:30');
            return slots;
        }

        // Time picker functions
        function openTimePicker(fieldId) {
            currentTimeField = fieldId;
            const currentTime = document.getElementById(fieldId).value;
            if (currentTime) {
                const [time, period] = convertTo12Hour(currentTime);
                const [hours, minutes] = time.split(':');
                selectedHour = parseInt(hours);
                selectedMinute = parseInt(minutes);
                selectedPeriod = period;
            }
            populateTimePicker();
            document.getElementById('timePickerModal').style.display = 'flex';
            document.getElementById('timePickerTitle').textContent = `Select ${fieldId.replace(/_/g, ' ').toUpperCase()}`;
            setTimeout(() => setupScrollListeners(), 200);
        }

        function closeTimePicker() {
            document.getElementById('timePickerModal').style.display = 'none';
            currentTimeField = null;
        }

        function populateTimePicker() {
            const hoursList = document.getElementById('hoursList');
            const minutesList = document.getElementById('minutesList');
            const periodList = document.getElementById('periodList');
            hoursList.innerHTML = '';
            minutesList.innerHTML = '';
            periodList.innerHTML = '';

            const hourValues = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
            const repeatedHours = [];
            for (let i = 0; i < 20; i++) repeatedHours.push(...hourValues);
            repeatedHours.forEach(hour => {
                const item = document.createElement('button');
                item.className = 'time-picker-item';
                item.dataset.value = hour;
                item.textContent = hour.toString().padStart(2, '0');
                item.onclick = () => selectTimeItem('hour', hour);
                hoursList.appendChild(item);
            });

            const minuteValues = [];
            for (let m = 0; m < 60; m += 5) minuteValues.push(m);
            const repeatedMinutes = [];
            for (let i = 0; i < 20; i++) repeatedMinutes.push(...minuteValues);
            repeatedMinutes.forEach(minute => {
                const item = document.createElement('button');
                item.className = 'time-picker-item';
                item.dataset.value = minute;
                item.textContent = minute.toString().padStart(2, '0');
                item.onclick = () => selectTimeItem('minute', minute);
                minutesList.appendChild(item);
            });

            for (let i = 0; i < 4; i++) {
                const spacer = document.createElement('div');
                spacer.className = 'time-picker-item time-picker-spacer';
                spacer.innerHTML = '&nbsp;';
                periodList.appendChild(spacer);
            }
            ['AM', 'PM'].forEach(period => {
                const item = document.createElement('button');
                item.className = 'time-picker-item';
                item.dataset.value = period;
                item.textContent = period;
                item.onclick = () => selectTimeItem('period', period);
                periodList.appendChild(item);
            });
            for (let i = 0; i < 4; i++) {
                const spacer = document.createElement('div');
                spacer.className = 'time-picker-item time-picker-spacer';
                spacer.innerHTML = '&nbsp;';
                periodList.appendChild(spacer);
            }

            setTimeout(() => {
                const hoursMiddle = Math.floor(hoursList.scrollHeight / 2);
                const minutesMiddle = Math.floor(minutesList.scrollHeight / 2);
                hoursList.scrollTop = hoursMiddle;
                minutesList.scrollTop = minutesMiddle;
                scrollToValue(hoursList, selectedHour, 'hour', true);
                scrollToValue(minutesList, selectedMinute, 'minute', true);
                centerPeriod(selectedPeriod);
            }, 100);
        }

        function centerPeriod(period) {
            const periodList = document.getElementById('periodList');
            const items = Array.from(periodList.querySelectorAll('.time-picker-item'));
            const targetItem = items.find(item => item.dataset.value === period);
            if (targetItem) {
                const containerHeight = periodList.clientHeight;
                const itemTop = targetItem.offsetTop;
                const itemHeight = targetItem.offsetHeight;
                periodList.scrollTop = itemTop - (containerHeight / 2) + (itemHeight / 2);
                updateSelectionVisual('period', period);
            }
        }

        function scrollToValue(container, value, type, instant = false) {
            const items = Array.from(container.querySelectorAll('.time-picker-item'));
            const center = container.getBoundingClientRect().top + container.clientHeight / 2;
            const matching = items.filter(i => {
                if (type === 'period') return i.dataset.value === value;
                return parseInt(i.dataset.value) === value;
            });
            if (matching.length) {
                let closest = matching[0];
                let minDist = Infinity;
                matching.forEach(item => {
                    const rect = item.getBoundingClientRect();
                    const mid = rect.top + rect.height / 2;
                    const dist = Math.abs(center - mid);
                    if (dist < minDist) {
                        minDist = dist;
                        closest = item;
                    }
                });
                if (closest) {
                    closest.scrollIntoView({
                        behavior: instant ? 'auto' : 'smooth',
                        block: 'center'
                    });
                }
            }
            updateSelectionVisual(type, value);
        }

        function selectTimeItem(type, value) {
            if (type === 'hour') {
                selectedHour = value;
                scrollToValue(document.getElementById('hoursList'), value, type);
            } else if (type === 'minute') {
                selectedMinute = value;
                scrollToValue(document.getElementById('minutesList'), value, type);
            } else if (type === 'period') {
                selectedPeriod = value;
                centerPeriod(value);
            }
        }

        function setupScrollListeners() {
            const hoursList = document.getElementById('hoursList');
            const minutesList = document.getElementById('minutesList');
            const periodList = document.getElementById('periodList');

            if (!hoursList.dataset.added) {
                hoursList.addEventListener('scroll', () => {
                    handleInfiniteScroll(hoursList, 'hour');
                    scheduleCenterAfterScroll(hoursList);
                });
                hoursList.dataset.added = true;
            }

            if (!minutesList.dataset.added) {
                minutesList.addEventListener('scroll', () => {
                    handleInfiniteScroll(minutesList, 'minute');
                    scheduleCenterAfterScroll(minutesList);
                });
                minutesList.dataset.added = true;
            }

            // FIX FOR PERIOD LIST AUTO-CENTERING
            if (!periodList.dataset.added) {
                periodList.addEventListener('scroll', () => {
                    updateSelectedFromScroll(periodList, 'period');
                    scheduleCenterAfterScroll(periodList);
                });
                periodList.dataset.added = true;
            }
        }


        // Debounced centering: after user stops scrolling, center the .selected item
        function scheduleCenterAfterScroll(container) {
            try {
                // clear previous timer
                if (container._centerTimer) clearTimeout(container._centerTimer);
                container._centerTimer = setTimeout(() => {
                    // find selected item in this container
                    const sel = container.querySelector('.time-picker-item.selected');
                    if (sel) {
                        // Smoothly center the selected item
                        sel.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    } else {
                        // If none selected, try to compute closest and center it
                        const items = Array.from(container.querySelectorAll('.time-picker-item'));
                        if (items.length) {
                            const center = container.getBoundingClientRect().top + container.clientHeight / 2;
                            let closest = null;
                            let minDist = Infinity;
                            items.forEach(item => {
                                const rect = item.getBoundingClientRect();
                                const mid = rect.top + rect.height / 2;
                                const dist = Math.abs(center - mid);
                                if (dist < minDist) { minDist = dist; closest = item; }
                            });
                            if (closest) closest.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    }
                }, 120);
            } catch (e) {
                console.error('scheduleCenterAfterScroll error', e);
            }
        }

        function handleInfiniteScroll(container, type) {
            // Disable infinite scroll for AM/PM list
            if (type === 'period') {
                updateSelectedFromScroll(container, type);
                return;
            }

            if (container.dataset.isAdjusting === 'true') return;

            const scrollTop = container.scrollTop;
            const scrollHeight = container.scrollHeight;
            const clientHeight = container.clientHeight;
            const maxScroll = scrollHeight - clientHeight;
            const buffer = clientHeight * 0.5;

            if (scrollTop < buffer) {
                container.dataset.isAdjusting = 'true';
                const offset = scrollTop;
                container.scrollTop = (scrollHeight / 2) + offset;
                setTimeout(() => { delete container.dataset.isAdjusting; }, 100);
            } else if (scrollTop > maxScroll - buffer) {
                container.dataset.isAdjusting = 'true';
                const offset = scrollTop - maxScroll;
                container.scrollTop = (scrollHeight / 2) + offset;
                setTimeout(() => { delete container.dataset.isAdjusting; }, 100);
            }

            updateSelectedFromScroll(container, type);
        }


        function updateSelectedFromScroll(container, type) {
            const items = Array.from(container.querySelectorAll('.time-picker-item'));
            const center = container.getBoundingClientRect().top + container.clientHeight / 2;

            let closest = null;
            let minDist = Infinity;

            items.forEach(item => {
                // skip blank spacers
                if (item.classList.contains('time-picker-spacer')) return;

                const rect = item.getBoundingClientRect();
                const mid = rect.top + rect.height / 2;
                const dist = Math.abs(center - mid);

                if (dist < minDist) {
                    minDist = dist;
                    closest = item;
                }
            });

            if (!closest) return;

            if (type === 'period') {
                selectedPeriod = closest.dataset.value;
                updateSelectionVisual('period', selectedPeriod);
            } else {
                const val = parseInt(closest.dataset.value);
                if (!isNaN(val)) {
                    if (type === 'hour') selectedHour = val;
                    if (type === 'minute') selectedMinute = val;
                    updateSelectionVisual(type, val);
                }
            }
        }


        function updateSelectionVisual(type, value) {
            const id = type === 'hour' ? 'hoursList'
                    : type === 'minute' ? 'minutesList'
                    : 'periodList';

            const list = document.getElementById(id);
            if (!list) return;

            const items = Array.from(list.querySelectorAll('.time-picker-item'));
            const center = list.getBoundingClientRect().top + list.clientHeight / 2;

            items.forEach(item => item.classList.remove('selected'));

            const matching = items.filter(item => {
                if (item.classList.contains('time-picker-spacer')) return false;   // ignore blanks
                if (type === 'period') return item.dataset.value === value;
                return parseInt(item.dataset.value) === value;
            });

            if (!matching.length) return;

            let closest = matching[0];
            let minDist = Infinity;

            matching.forEach(item => {
                const rect = item.getBoundingClientRect();
                const mid = rect.top + rect.height / 2;
                const dist = Math.abs(center - mid);
                if (dist < minDist) {
                    minDist = dist;
                    closest = item;
                }
            });

            closest.classList.add('selected');
        }

        function confirmTimeSelection() {
            if (!currentTimeField) return;
            const time24 = convertTo24Hour(selectedHour, selectedMinute, selectedPeriod);
            const display = `${selectedHour.toString().padStart(2, '0')}:${selectedMinute.toString().padStart(2, '0')} ${selectedPeriod}`;
            // Enforce allowed window 07:30 - 21:30 on client side
            try {
                const [h, m] = time24.split(':').map(Number);
                const minutes = h * 60 + m;
                const minAllowed = 7 * 60 + 30;
                const maxAllowed = 21 * 60 + 30;
                if (minutes < minAllowed || minutes > maxAllowed) {
                    showAlert('Allowed schedule window is 07:30 to 21:30. Please choose a time within this range.', 'error');
                    return;
                }
            } catch (e) {
                // If parsing fails, still allow model/server to validate
            }

            document.getElementById(currentTimeField).value = time24;
            document.getElementById(`${currentTimeField}_display`).textContent = display;
            if (currentTimeField.startsWith('edit_')) {
                filterAvailableInstructors('edit_faculty_select');
                // Update duration and validate when time changes in edit modal
                updateDurationDisplayEdit();
            } else {
                filterAvailableInstructors('faculty_select');
                // Update duration and validate when time changes in create modal
                updateDurationDisplay();
                // Re-filter available days based on new time
                filterAvailableDays();
            }
            closeTimePicker();
        }

        function convertTo12Hour(t) {
            const [h, m] = t.split(':').map(Number);
            const period = h >= 12 ? 'PM' : 'AM';
            const h12 = h % 12 || 12;
            return [`${h12.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`, period];
        }

        function formatTimeLabel(timeStr) {
            if (!timeStr) return '';
            const [time12, period] = convertTo12Hour(timeStr);
            return `${time12} ${period}`;
        }

        function convertTo24Hour(h12, m, p) {
            let h = h12;
            if (p === 'PM' && h12 !== 12) h += 12;
            if (p === 'AM' && h12 === 12) h = 0;
            return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
        }

        function setTimeDisplay(fieldId) {
            const input = document.getElementById(fieldId);
            const display = document.getElementById(`${fieldId}_display`);
            if (!input || !display) return;
            const [time12, period] = convertTo12Hour(input.value || '07:30');
            display.textContent = `${time12} ${period}`;
        }

        // Utility functions
        function filterSections() {
            const searchInput = document.getElementById('searchInput').value.toLowerCase();
            const sectionCards = document.querySelectorAll('.section-card');
            sectionCards.forEach(card => {
                const name = card.dataset.sectionName || '';
                const curriculum = card.dataset.curriculum || '';
                if (name.includes(searchInput) || curriculum.includes(searchInput)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        function toggleSectionMenu(event, sectionId) {
            event.stopPropagation();
            document.querySelectorAll('.section-dropdown-menu').forEach(menu => {
                if (menu.id !== `sectionMenu${sectionId}`) {
                    menu.classList.remove('show');
                }
            });
            const menu = document.getElementById(`sectionMenu${sectionId}`);
            if (menu) menu.classList.toggle('show');
        }

        function toggleDropdown(event) {
            if (event && event.stopPropagation) event.stopPropagation();
            const trigger = event ? (event.currentTarget || event.target.closest('.account-section') || event.target.closest('.admin-section')) : null;
            const dropdown = (trigger && (trigger.querySelector('.account-dropdown-menu') || trigger.querySelector('.dropdown-menu'))) || document.querySelector('.account-dropdown-menu') || document.querySelector('.dropdown-menu');
            if (dropdown) dropdown.classList.toggle('show');
        }

        function toggleStatus(event, sectionId) {
            event.stopPropagation();
            if (!confirm('Are you sure you want to toggle the status of this section?')) return;
            fetchWithCSRF(`/admin/section/${sectionId}/toggle-status/`, {
                method: 'POST'
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const statusElement = document.getElementById(`status-${sectionId}`);
                    statusElement.textContent = data.status_display;
                    statusElement.style.color = data.status === 'complete' ? '#28a745' : '#dc3545';
                    showAlert('Status updated successfully!', 'success');
                } else {
                    showAlert('Error updating status', 'error');
                }
            })
            .catch(err => {
                console.error('toggleStatus error', err);
                showAlert('Error updating status', 'error');
            });
        }

        function openEditSectionModal(sectionId) {
            // Open the inline edit modal on the schedule page by fetching the
            // section data and populating the modal fields.
            fetch(`/admin/section/edit/${sectionId}/`)
                .then(res => {
                    if (!res.ok) throw new Error('Network response not ok');
                    return res.json();
                })
                .then(data => {
                    // If endpoint returned success=false, handle gracefully
                    if (data.success === false) {
                        showAlert('Unable to load section data for editing.', 'error');
                        return;
                    }

                    // Populate modal fields (IDs match those used in schedule.html)
                    document.getElementById('edit_section_id').value = data.id;
                    document.getElementById('edit_name').value = data.name;
                    // curriculum may be an id
                    try {
                        const curSel = document.getElementById('edit_curriculum');
                        if (curSel) curSel.value = data.curriculum;
                    } catch (e) {}
                    document.getElementById('edit_year_level').value = data.year_level;
                    document.getElementById('edit_semester').value = data.semester;
                    document.getElementById('edit_max_students').value = data.max_students;

                    openModal('editSectionModal');
                })
                .catch(err => {
                    console.error('openEditSectionModal error', err);
                    showAlert('Error loading section for edit', 'error');
                });
        }

        function deleteSection(sectionId, sectionName) {
            if (!confirm(`Are you sure you want to delete section ${sectionName}? This action cannot be undone.`)) return;
            fetchWithCSRF(`/admin/section/delete/${sectionId}/`, {
                method: 'POST'
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showAlert(`Section ${sectionName} deleted successfully!`, 'success');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    const err = data.errors ? data.errors.join(', ') : 'Unknown error';
                    showAlert(`Error deleting section: ${err}`, 'error');
                }
            })
            .catch(err => {
                console.error('deleteSection error', err);
                showAlert('Error deleting section', 'error');
            });
        }

        // Submit edit section form from schedule page
        function submitEditSectionFromSchedule(event) {
            event.preventDefault();
            const form = document.getElementById('editSectionForm');
            const formData = new FormData(form);
            const sectionId = formData.get('section_id') || document.getElementById('edit_section_id').value;

            // Validate name format: CPE[year][semester]S[number]
            const sectionName = formData.get('name');
            const pattern = /^([A-Z]+)(\d)(\d)S(\d+)$/;
            const match = sectionName.match(pattern);
            if (!match) {
                showAlert('Section name must follow format: CPE[year][semester]S[number] Example: CPE11S1', 'error');
                return;
            }

            fetchWithCSRF(`/admin/section/edit/${sectionId}/`, {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showAlert('Section updated successfully!', 'success');
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    const err = data.errors ? data.errors.join('\n') : 'Error updating section';
                    showAlert(err, 'error');
                }
            })
            .catch(err => {
                console.error('submitEditSectionFromSchedule error', err);
                showAlert('Error updating section', 'error');
            });
        }

        function exportSchedule() {
            if (!currentSectionId) {
                showAlert('Please select a section first', 'warning');
                return;
            }
            const url = `/admin/section/${currentSectionId}/schedule/print/`;
            window.open(url, '_blank');
        }

        function deleteAllSchedule() {
            if (!currentSectionId) {
                showAlert('Please select a section first', 'warning');
                return;
            }

            if (!confirm('Delete all schedules for this section? This cannot be undone.')) {
                return;
            }

            fetchWithCSRF(`/admin/section/${currentSectionId}/delete-schedules/`, {
                method: 'POST'
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const message = data.deleted_count
                        ? `Deleted ${data.deleted_count} schedules.`
                        : data.message || 'No schedules found to delete.';
                    showAlert(message, 'success');
                    const sectionName = document.getElementById('scheduleSectionName').textContent;
                    const curriculum = document.getElementById('scheduleCurriculum').textContent;
                    loadScheduleView(currentSectionId, sectionName, curriculum);
                } else {
                    showAlert(data.error || 'Unable to delete schedules.', 'error');
                }
            })
            .catch(err => {
                console.error('deleteAllSchedule error', err);
                showAlert('Unable to delete schedules.', 'error');
            });
        }

        function printSchedule() {
            if (!currentSectionId) {
                showAlert('Please select a section first', 'warning');
                return;
            }
            const url = `/admin/section/${currentSectionId}/schedule/print/`;
            window.open(url, '_blank');
        }

        // Close dropdowns when clicking outside
        document.addEventListener('click', (event) => {
            if (!event.target.closest('.admin-section') && !event.target.closest('.account-section') && !event.target.closest('.dropdown-menu')) {
                document.querySelectorAll('.account-dropdown-menu, .dropdown-menu').forEach(m => m.classList.remove('show'));
            }
            if (!event.target.closest('.dropdown-menu-container')) {
                document.querySelectorAll('.section-dropdown-menu').forEach(menu => {
                    menu.classList.remove('show');
                });
            }
        });