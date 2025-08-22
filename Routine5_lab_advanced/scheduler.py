def schedule_classes(teachers, classes, days, time_slots):
    schedule = {day: {slot: None for slot in time_slots} for day in days}
    teacher_schedule = {teacher: {day: [] for day in days} for teacher in teachers}
    
    # Try to schedule single classes first
    for cls in classes:
        scheduled = False
        for day in days:
            for slot in time_slots:
                if schedule[day][slot] is None and len(teacher_schedule[cls['teacher']][day]) == 0:
                    schedule[day][slot] = cls
                    teacher_schedule[cls['teacher']][day].append(slot)
                    scheduled = True
                    break
            if scheduled:
                break
        
        # If not scheduled, allow double class
        if not scheduled:
            for day in days:
                if len(teacher_schedule[cls['teacher']][day]) == 1:
                    for slot in time_slots:
                        if schedule[day][slot] is None:
                            schedule[day][slot] = cls
                            teacher_schedule[cls['teacher']][day].append(slot)
                            scheduled = True
                            break
                if scheduled:
                    break
    
    return schedule

# Example usage
teachers = ['Teacher1', 'Teacher2']
classes = [
    {'name': 'Math', 'teacher': 'Teacher1'},
    {'name': 'Science', 'teacher': 'Teacher1'},
    {'name': 'English', 'teacher': 'Teacher2'}
]
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00']

result = schedule_classes(teachers, classes, days, time_slots)
for day, slots in result.items():
    print(f"{day}: {slots}")