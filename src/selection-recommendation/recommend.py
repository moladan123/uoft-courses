import sys
sys.path.append("../util")
import itertools
import Database
import time_conflicts_check

DB_NAME = "uoftcourses"
DB_PATH = "../../database.info"


def __get_all_possible_course_times(course_code, campus):
    """
    course_code: a string e.g. "CSC148"
    campus: a string - either "St. George", "Scarborough", or "Mississauga"
    Returns a tuple:
        - the first element is a list of strings containing all possible times (i.e. no conflicts) of combinations of lecture/tutorial/lab sections.
          For the format of the strings, see the process_times() function in the time_conflicts_check module
        - the second element is a list of strings representing the respective lecture, tutorial and lab sections

    Sample outputs:

        (['THURSDAY 13:00-16:00', 'THURSDAY 18:00-21:00'], ['CSC108 Lec 0101', 'CSC108 Lec 5101'])
        Here, because the lists have length 2, there are two possible combinations of course sections. Each of these
        combinations has only one section - a lecture.

        (['FRIDAY 14:00-16:00 WEDNESDAY 14:00-16:00 MONDAY 14:00-16:00 MONDAY 16:00-18:00 WEDNESDAY 16:00-18:00'], ['APS105 Lec 0101 APS105 Lec 0101 APS105 Lec 0101 APS105 Tut 0101 APS105 Pra 0101'])
        Here, because the lists have length 1, there is only one possible combination of course sections.
        This combination consists of 3 lecture sections, 1 tutorial section, and 1 practical section.

    Note that the indices of the two lists correspond. For example, the first element of the first list has times that correspond
    to the class sections in the first element of the second list.
    """
    connection = Database.get_connection(DB_PATH, DB_NAME)
    cursor = connection.cursor()
    all_course_data = Database.get_course_data_by_cID_and_campus(cursor, course_code, campus)

    lecture_times = []
    lecture_sections = []
    tutorial_times = []
    tutorial_sections = []
    lab_times = []
    lab_sections = []

    for course_data in all_course_data:
        lec_num = course_data[10]
        lec_comps = lec_num.split(" ")
        lec_time = course_data[11]

        thing_to_append = []
        for i in range(len(lec_time.split(" "))//2):
            thing_to_append.append(course_code + " " + lec_num)
        thing_to_append = " ".join(thing_to_append)

        if lec_comps[0] == "Lec":
            lecture_times.append(lec_time)
            lecture_sections.append(thing_to_append)
        elif lec_comps[0] == "Tut":
            tutorial_times.append(lec_time)
            tutorial_sections.append(thing_to_append)
        elif lec_comps[0] == "Pra":
            lab_times.append(lec_time)
            lab_sections.append(thing_to_append)
        else:  # shouldn't happen
            raise ValueError

    all_possible_times = []
    all_possible_section_combs = []

    # course has both tutorial and lab sections
    if (tutorial_times != []) and (lab_times != []):
        all_times = list(itertools.product(lecture_times, tutorial_times, lab_times))  # all combinations of lecture/tutorial/lab
        all_section_combs = list(itertools.product(lecture_sections, tutorial_sections, lab_sections))

        for i in range(len(all_times)):
            if (time_conflicts_check.no_time_conflict(all_times[i][0], all_times[i][1])  # check for internal time conflicts
                    and time_conflicts_check.no_time_conflict(all_times[i][0], all_times[i][2])
                    and time_conflicts_check.no_time_conflict(all_times[i][1], all_times[i][2])):
                all_possible_times.append(" ".join(all_times[i]))
                all_possible_section_combs.append(" ".join(all_section_combs[i]))

    # course has lab sections but no tutorial sections
    elif (tutorial_times == []) and (lab_times != []):
        all_times = list(itertools.product(lecture_times, lab_times))  # all combinations of lecture/lab
        all_section_combs = list(itertools.product(lecture_sections, lab_sections))

        for i in range(len(all_times)):
            if time_conflicts_check.no_time_conflict(all_times[i][0], all_times[i][1]):  # check for internal time conflicts
                all_possible_times.append(" ".join(all_times[i]))
                all_possible_section_combs.append(" ".join(all_section_combs[i]))

    # course has tutorial sections but no lab sections
    elif (tutorial_times != []) and (lab_times == []):
        all_times = list(itertools.product(lecture_times, tutorial_times))  # all combinations of lecture/tutorial
        all_section_combs = [list(i) for i in list(itertools.product(lecture_sections, tutorial_sections))]

        for i in range(len(all_times)):
            if time_conflicts_check.no_time_conflict(all_times[i][0], all_times[i][1]):  # check for internal time conflicts
                all_possible_times.append(" ".join(all_times[i]))
                all_possible_section_combs.append(" ".join(all_section_combs[i]))

    # course only has lecture sections
    else:
        all_possible_times = lecture_times
        all_possible_section_combs = lecture_sections

    return(all_possible_times, all_possible_section_combs)


def create_schedule(campus, *args):
    """
    campus: a string - either "St. George", "Scarborough", or "Mississauga"
    args: strings of course codes e.g. "CSC148", "COG250"
    Returns a tuple:
        - the first element is a list of strings containing all possible times (i.e. no conflicts) of combinations of course sections.
          For the format of the strings, see the process_times() function in the time_conflicts_check module
        - the second element is a list of strings representing the respective course sections

    Sample output:

        (['MONDAY 18:00-20:00 THURSDAY 18:00-21:00 TUESDAY 18:00-21:00 WEDNESDAY 18:00-20:00'], ['CSC148 Lec 5101 CSC148 Lec 5101 CSC165 Lec 5101 CSC165 Lec 5101'])

        Here, because the lists have length 1, there is only one possible combination of course sections. Note that the sections in the second list
        are given in the same order as the times in the first list. The times and sections are all delimited by spaces.

    The output times and sections will be all the schedules comprised of a combination of sections from the input courses
    with no time conflicts. If no such combinations exist, the return value is a tuple of two empty lists.
    """
    all_times = []
    all_sections = []
    all_course_times = []
    all_course_sections = []

    for course_code in args:
        course_times, course_sections = __get_all_possible_course_times(course_code, campus)
        all_course_times.append(course_times)
        all_course_sections.append(course_sections)

    times_combs = list(itertools.product(*all_course_times))
    sections_combs = list(itertools.product(*all_course_sections))

    for i in range(len(times_combs)):
        has_conflicts = False
        time_comb = times_combs[i]

        for j in range(0, len(time_comb) - 1):
            for k in range(j + 1, len(time_comb)):
                if not time_conflicts_check.no_time_conflict(time_comb[j], time_comb[k]):
                    has_conflicts = True
                    break
            if has_conflicts:
                break
        if has_conflicts:
            break

        all_times.append(" ".join(times_combs[i]))
        all_sections.append(" ".join(sections_combs[i]))

    return(all_times, all_sections)


def day_to_int(day):
    """
    day: a string representing the day of the week
    Returns an integer

    e.g. "MONDAY" -> 0, "TUESDAY" -> 1, etc.
    """
    days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    return days.index(day.upper())


def process_schedule(all_times, all_sections):
    """
    all_times: a string representing the times the courses take place
    all_sections: a string representing the sections that take place during those times

    all_times and all_sections are simply taken as output from the create_schedule() function

    Returns a 2D list representing a schedule in the following format:
        [Monday_schedule, Tuesday_schedule, Wednesday_schedule, Thursday_schedule, Friday_schedule]
        The elements of this list have 14 elements each. Each of these elements is a course section that takes place
        during that hour, with index 0 representing 8am-9am and index 13 representing 9pm-10pm, or None if no course takes
        place during that time.

    e.g. process_schedule(
            "MONDAY 18:00-20:00 THURSDAY 18:00-21:00 TUESDAY 18:00-21:00 WEDNESDAY 18:00-20:00",
            "CSC148 Lec 5101 CSC148 Lec 5101 CSC165 Lec 5101 CSC165 Lec 5101")
        -> [
               [None, None, None, None, None, None, None, None, None, None, 'CSC148 Lec 5101', 'CSC148 Lec 5101', None, None],
               [None, None, None, None, None, None, None, None, None, None, 'CSC165 Lec 5101', 'CSC165 Lec 5101', 'CSC165 Lec 5101', None],
               [None, None, None, None, None, None, None, None, None, None, 'CSC165 Lec 5101', 'CSC165 Lec 5101', None, None],
               [None, None, None, None, None, None, None, None, None, None, 'CSC148 Lec 5101', 'CSC148 Lec 5101', 'CSC148 Lec 5101', None],
               [None, None, None, None, None, None, None, None, None, None, None, None, None, None]
           ]
    """
    week = []
    day = [None]*14
    for i in range(5):  # week = day[:]*5 doesn't work for some reason
        week.append(day[:])

    times = all_times.split(" ")
    sections = all_sections.split(" ")

    for i in range(len(times)//2):
        start_end = times[2*i + 1].split("-")
        start = time_conflicts_check.time_to_num(start_end[0]) - 8
        dur = time_conflicts_check.time_to_num(start_end[1]) - time_conflicts_check.time_to_num(start_end[0])

        for hour in range(dur):
            week[day_to_int(times[2*i])][start + hour] = " ".join(sections[3*i:3*i + 3])

    return week


def get_best_schedule(campus, *args):  # waiting for a finished cost function to use this functino
    """
    best_schedule = []
    best_score = []
    possible_schedules = create_schedule(campus, *args)

    for i in range(len(possible_schedules[0])):
        schedule = process_schedule(possible_schedules[0][i])
        score =  # some sort of cost function
        if score > best_score:
            best_schedule = schedule
            best_score = score

    return best_schedule
    """
