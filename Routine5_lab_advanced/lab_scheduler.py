# Enhanced function to check consecutive lab times and enforce morning/afternoon alternation
def check_consecutive_lab_times(day, temp_slots, section_lab_times, days):
    day_idx = days.index(day)
    
    # Define morning and afternoon slots
    morning_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00']
    afternoon_slots = ['13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00']
    
    current_is_morning = any(slot in morning_slots for slot in temp_slots)
    
    # Check previous day
    if day_idx > 0:
        prev_day = days[day_idx - 1]
        if prev_day in section_lab_times:
            prev_slots = section_lab_times[prev_day]
            prev_is_morning = any(slot in morning_slots for slot in prev_slots)
            
            # If previous day had morning lab and current is also morning, return conflict
            # If previous day had afternoon lab and current is also afternoon, return conflict
            if prev_is_morning == current_is_morning:
                return True
    
    # Check next day
    if day_idx < len(days) - 1:
        next_day = days[day_idx + 1]
        if next_day in section_lab_times:
            next_slots = section_lab_times[next_day]
            next_is_morning = any(slot in morning_slots for slot in next_slots)
            
            # If next day has same time period (morning/afternoon), return conflict
            if next_is_morning == current_is_morning:
                return True
    
    return False

# Usage: if check_consecutive_lab_times(day, temp_slots, section_lab_times, days): continue