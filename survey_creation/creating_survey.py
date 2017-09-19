#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = 'Olivier Philippe'


"""
Limesurvey offers the possibility to import/export a TSV file containing all the information
of the survey structure. Using this possibility, this script aims to translate the files used
by the different groups to creates their survey, into a compatible TSV file.
It take only the argument of the folder where all the information is stored, and create a new
compatible file.
All information about the TSV file structure can be retrieved here:
    https://manual.limesurvey.org/Tab_Separated_Value_survey_structure
"""

import csv
import sys
import os
from collections import OrderedDict
from include.logger import logger
from config.config import creationConfig as main_config
import importlib
from random import shuffle
from markdown import markdown

RUNNING = 'dev'

if RUNNING == 'dev':
    DEBUGGING='DEBUG'
elif RUNNING == 'prod':
    DEBUGGING='INFO'

logger = logger(name='creating survey', stream_level=DEBUGGING)


class surveyCreation:
    """
    Creating a text file for limesurvey that can be imported, using the
    resources in the csv files and in the different folders for each
    country's project
    """

    def __init__(self, project):
        """
        Get the project name (folder).
        Import the associated config file
        Create the outfile path
        :params:
            :project str(): the name of which folder/project the information
                is stored
        """
        self.project = project
        self.specific_config = self.import_config()

    def import_config(self):
        """
        Import the config file associated with the folder name
        """
        module = 'config.{}'.format(self.project)
        return importlib.import_module(module).config()

    def init_outfile(self):
        """
        Rewrite over the existing file to avoid issue of appending and
        return the path to the file
        """
        outfile_name = self.project + '_to_import.txt'
        outfile = os.path.join(self.project, outfile_name)
        with open(outfile, 'w') as f:
            w = csv.DictWriter(f, delimiter='\t',
                               lineterminator='\n',
                               quotechar='"',
                               fieldnames=main_config.main_headers)
            w.writeheader()
        return outfile

    @staticmethod
    def _to_modify(original_list, modified_list):
        """
        """
        return_list = list()
        for element in original_list:
            to_replace = False
            for e in modified_list:
                if element['name'] == e['name']:
                    return_list.append(e)
                    to_replace = True
                    break
            if to_replace is False:
                return_list.append(element)
        return return_list

    @staticmethod
    def _to_add(original_list, list_to_add):
        """
        """
        for obj in list_to_add:
            original_list.insert(obj[1], obj[0])
        return original_list

    def _write_row(self, row):
        """
        Append a dictionary (a row) to the outfile.
        The dictionary as to respected the keys structure
        found in the main_config.main_headers
        As the format accepted by limesurvey is tsv, the
        separator as setup to be tabulation ('\t')
        :params:
            :row dict(): containing the information to record
                in the file

        :return: None, record into the self.outfile
        """
        with open(self.outfile, 'a') as f:
            w = csv.DictWriter(f, delimiter='\t',
                               lineterminator='\n',
                               quotechar='"',
                               fieldnames=main_config.main_headers)
            w.writerow(row)

    def _record_list(self, list_to_copy):
        """
        Get a list of dictionary to add into the outfile.
        Get each dictionary and update the empty dictionary created
        by create_empty_row() to be sure all the headers and element are
        set up (with '' if empty)
        :params:
            :list_to_copy list(): List of dictionary to record

        :return:
            :None: record each dict from the list into the self.outfile
        """
        def create_empty_row():
            """
            Create an Ordered dictionary to be used to translate csv file to tsv
            """
            return OrderedDict((k, '') for k in main_config.main_headers)
        for element in list_to_copy:
            row = create_empty_row()
            row.update(element)
            self._write_row(row)

    def create_header(self):
        """
        Create the headers for the outfile. The
        headers are recorded in the main_config file.
        The specific_config file can also contain specific parameters
        to either modify or add to the headers dictionary before recording
        it into  the outfile.
        These headers needs to be added at the top of the outfile.
        The header needs to be recorded only once and does not change with
        the added translation in the case they are some

        :return:
            :None: writes the header into the outfile
        """
        # Create a copy the header to the empty file
        # Check if some parameters needs to be modify from the specific_config
        good_parameters = self._to_modify(main_config.global_headers, self.specific_config.header_to_modify)
        # Check if some parameters needs to be added.
        good_parameters = self._to_add(good_parameters, self.specific_config.header_to_add)
        # Record the copy into the file
        self._record_list(good_parameters)

    def _get_languages(self):
        """
        Add any languages to the list that are addition to english
        :return:
            :languages list(): all languages represented by their code
                the language 'en' is always the first element to the list
        """
        languages = main_config.languages
        languages.append(self.specific_config.languages_to_add)
        return languages

    @staticmethod
    def _add_text_message(full_list, message, type_message):
        """
        """
        return_list = list()
        message_done = False
        for element in full_list:
            if message_done is False:
                if element['name'] == 'surveyls_{}text'.format(type_message):
                    message_done = True
                    element['text'] = message
            return_list.append(element)
        return return_list

    def create_survey_settings(self):
        """
        """
        def get_text(type_message, lang=None):
            """
            """
            if lang and lang != 'en':
                filename = '{}_message_{}.md'.format(type_message, lang)
            else:
                filename = '{}_message.md'.format(type_message)

            folder = os.path.join(self.project, 'texts')
            path = os.path.join(folder, filename)
            with open(path, 'r') as f:
                return markdown(f.read())

        for lang in self.languages:
            # All these None are a workaround to fix the bug that add
            # two titles for the second language. No idea why
            survey_settings = None
            setting_with_lang = None
            survey_title = None
            survey_title_row = None
            # Get the welcome message
            welcome_message = get_text('welcome', lang)
            # Get the end message
            end_message = get_text('end', lang)
            survey_settings = self._to_modify(main_config.global_settings,
                                              self.specific_config.settings_to_modify)
            survey_settings = self._to_add(survey_settings,
                                           self.specific_config.settings_to_add)

            survey_title = self.specific_config.survey_title[lang]
            survey_title_row = {'class': 'SL', 'name': 'surveyls_title', 'text': survey_title}
            survey_settings.insert(0, survey_title_row)
            # print(survey_settings)
            survey_settings = self._add_text_message(survey_settings, welcome_message, 'welcome')
            survey_settings = self._add_text_message(survey_settings, end_message, 'end')

            # Add the appropriate language field for each of the dictionary
            setting_with_lang = list()
            for d in survey_settings:
                d['language'] = lang
                setting_with_lang.append(d)

            self._record_list(setting_with_lang)

    def check_adding_section(self, row, nbr_section, default_row, lang):
        if int(row['section']) - 1 != nbr_section:
            # -1 because the section numbers starts at 0 but
            # in the csv survey_file it starts at 1
            nbr_section = int(row['section']) - 1
            section = main_config.group_format
            # type/scale are like 'G0', 'G1', etc.
            section['type/scale'] = 'G' + str(nbr_section)
            section['language'] = lang
            section.update(default_row[nbr_section][lang])
            self._write_row(section)
        return nbr_section

    @staticmethod
    def read_survey_file(folder):
        """
        Read the survey csv file and yield each line as a dictionary
        """
        question_file = os.path.join(folder, '.'.join([folder, 'csv']))
        with open(question_file, 'r') as f:
            csv_f = csv.DictReader(f)
            for row in csv_f:
                yield row

    @staticmethod
    def group_likert(indict):
        """
        Take the dictionary of all the questions and group them
        into the same group if they have to be displayed together.
        Only applicable for the type_question Y/N/NA and the likert ones
        It also perform a check to see if a condition as been setup with
        the key 'condition'.
        In that case it does not group the questions
        """
        previous_answer_format = None
        previous_file_answer = None
        previous_code = None
        previous_file_answer = None
        previous_condition = None
        group_survey_q = list()
        for q in indict:
            current_answer_format = q['answer_format'].lower()
            current_file_answer = q['answer_file']
            current_code = ''.join([i for i in q['code'] if not i.isdigit()])
            # Checking if there is a condition. When not, it is an empty string ''
            if q['condition'] != '':
                current_condition = True
            else:
                current_condition = False

            if current_answer_format == 'likert' and current_condition is False:
                if len(group_survey_q) > 0:
                    if current_file_answer == previous_file_answer or previous_file_answer is None:
                        if previous_answer_format == 'likert':
                            pass
                        else:
                            yield group_survey_q
                            group_survey_q = list()
                    else:
                        yield group_survey_q
                        group_survey_q = list()

            elif current_answer_format == 'y/n/na' and current_condition is False:
                if len(group_survey_q) > 0:
                    if current_code == previous_code or previous_code is None:
                        if previous_answer_format == 'y/n/na':
                            pass
                        else:
                            yield group_survey_q
                            group_survey_q = list()
                    else:
                        yield group_survey_q
                        group_survey_q = list()

            else:
                if len(group_survey_q) > 0:
                    yield group_survey_q
                group_survey_q = list()
            group_survey_q.append(q)
            previous_answer_format = current_answer_format
            previous_file_answer = current_file_answer
            previous_code = current_code

        yield group_survey_q

    @staticmethod
    def get_answer(folder, file_answer):
        """
        """
        outfile = os.path.join(folder, 'listAnswers', '{}.csv'.format(file_answer))
        with open(outfile, 'r') as f:
            return [x[:-1] for x in f.readlines()]

    def setup_question(self, type_question, row, txt_lang, lang):
        """
        Return a formatted dictionary with the shared information
        accross all questions
        """
        if type_question == 'multi_likert':
            question = main_config.likert_question
        elif type_question == 'one choice':
            question = main_config.one_choice_question
        elif type_question == 'ranking':
            question = main_config.ranking_question
        elif type_question == 'multiple choice':
            question = main_config.multiple_choice_question
        elif type_question == 'freenumeric':
            question = main_config.freenumeric_question
        elif type_question == 'freetext':
            question = main_config.freetext_question
        elif type_question == 'likert':
            question = main_config.likert_question
        elif type_question == 'y/n/na':
            question = main_config.y_n_question
        else:
            print(type_question)
            raise

        if type_question == 'multi_likert':
            # If multi likert it means the questions are presented in an array
            # where the header is the header for the arrays and all questions
            # are created during the subquestion process. In consequences
            # The questions here cannot have the row['text'] as for the other
            # type of questions but rather an unique id that is ensure
            # by incrementing the self.code_to_multiple_question.
            question['name'] = 'likert' + str(self.code_to_multiple_question)
            self.code_to_multiple_question +=1
            question['text'] = ''
        else:
            question['name'] = row['code']
            question['text'] = row[txt_lang]

        question['language'] = lang

        if row['other'] == 'Y':
            question['other'] = 'Y'
        else:
            question['other'] = 'N'

        self._write_row(question)

    def setup_subquestion(self, type_question, lang, list_likert=None, txt_lang=None):
        """
        """

        if type_question == 'multi_likert':
            for row in list_likert:
                subquestion = main_config.subquestion
                subquestion['relevance'] = '1'
                subquestion['language'] = lang
                subquestion['name'] = row['code']
                subquestion['text'] = row[txt_lang]
                self._write_row(subquestion)

        if type_question == 'ranking':
            # Create the Subquestion ranks
            for i in range(1, 9):  # To get 8 ranked questions
                subquestion = main_config.subquestion
                subquestion['name'] = str(i)
                subquestion['text'] = 'Rank' + str(i)
                subquestion['language'] = lang
                subquestion['relevance'] = '1'
                self._write_row(subquestion)

        if type_question == 'likert':
            # Need to create an  empty subquestion
            subquestion = main_config.subquestion
            subquestion['name'] = 'SQ001'
            subquestion['relevance'] = '1'
            subquestion['language'] = lang
            self._write_row(subquestion)

    def setup_answer(self, type_question, row, index_lang, lang):
        """
        Create the answer itself
        """
        n = 1
        for text_answer in self.get_answer(self.project, row['answer_file']):
            if type_question == 'one choice':
                answer_row = main_config.one_choice_answer
            elif type_question == 'multi choice':
                answer_row = main_config.multiple_choice_answer
            elif type_question == 'likert':
                answer_row = main_config.likert_answer
            elif type_question == 'ranking':
                answer_row = main_config.ranking_answer
            # answer_row['name'] = 'A' + str(n)
            answer_row['name'] = str(n)
            # to get the translation  of the answers. If there is None, it takes the first
            # element (the english one). Needed because sometimes, the answers are not translated
            try:
                answer_row['text'] = text_answer.split(';')[index_lang].strip('"')
            except IndexError:
                answer_row['text'] = text_answer.split(';')[0].strip('"')
            answer_row['language'] = lang
            self._write_row(answer_row)
            n +=1

    def get_txt_lang(self, lang, index_lang):
        """
        Return the right txt key when a translation is pickup
        if it is in English, the key is only 'question', but in
        case of translation it is 'lang_trans'.format(int) for all
        the language the survey has. The order of the languages in the
        main csv file needs to be the same order as in the config file
        params:
            :lang str(): the code of the language used
            :index_lang int(): the number to know which translation it is
        return:
            :str(): the key used later to access the text of the question
        """
        # Speficify where to find the text for the question
        if lang != 'en':
            return 'lang_trans' + str(index_lang)
        else:
            return 'question'

    def setup_condition(self, condition):
        """
        """
        def split_list(inlist, logical_element):
            return [i.strip() for i in list_to_compare.lower().split(logical_element.lower())]

        def remove_unused_word(word):
            return word.replace('in', '').strip()

        # First check if there is a list in the field
        if '[' in condition:
            element_to_compare = condition.split('[')[0]
            list_to_compare = condition.split('[')[1].replace(']', '')
            if 'OR' in list_to_compare:
                logical_element = 'or'
            if 'AND' in list_to_compare:
                logical_element = 'and'
            list_to_compare = split_list(list_to_compare, logical_element)
            element_to_compare = remove_unused_word(element_to_compare)
            # print(element_to_compare)
            # print(list_to_compare)
        else:  # no list, only several element or several conditions
            pass
            # Check if there is Or or AND
            # if 'or' in condition.lower():
            # elif 'AND' in condition:
                # print(condition)
        if condition != '':
            print(condition)
        # and_list = condition.split('AND')
        # print('And list')
        # print(and_list)
        # or_list = condition.split('OR')
        # print('OR list')
        # print(or_list)

    def create_survey_questions(self):
        """
        """
        # Create the questions for each languages, everything has to be done each time
        # the enumerate helps for finding the right answer and the right lang_trans
        # in case of more than one translation
        for index_lang, lang in enumerate(self.languages):
            txt_lang = self.get_txt_lang(lang, index_lang)
            # Add a first section
            nbr_section = -1
            nbr_section = self.check_adding_section({'section': 0}, nbr_section, self.specific_config.sections_txt,
                                                    lang)

            # Need this variable to inc each time a new multiple questions is created to ensure they are unique
            # only used in the case of likert and y/n/na merged together
            self.code_to_multiple_question = 0

            # Open the csv file and read it through a dictionary (generator)
            question_to_transform = self.read_survey_file(self.project)

            # pass this generator into the function group_likert() to group Y/N and likert together
            for q in self.group_likert(question_to_transform):

                # If questions were grouped together, need to change how it is process
                if len(q) > 1:
                    # Check if a new section needs to be added before processing the question
                    nbr_section = self.check_adding_section(q[0], nbr_section, self.specific_config.sections_txt, lang)

                    # Check if the list of items need to be randomize
                    # if it is the case, just use shuffle() to shuffle the list in-place
                    if q[0]['random'] == 'Y':
                        shuffle(q)

                    if q[0]['answer_format'].lower() == 'likert':

                        # Create the question header that needs to be created once for all the
                        # following question
                        self.setup_question('multi_likert', q[0], txt_lang, lang)
                        self.setup_subquestion('multi_likert', lang, q, txt_lang)
                        self.setup_answer('likert', q[0], index_lang, lang)

                    elif q[0]['answer_format'].lower() == 'y/n/na':
                        self.setup_question('y/n/na', q[0], txt_lang, lang)

                else:
                    for row in q:
                        # Check if a new section needs to be added before processing the question
                        nbr_section = self.check_adding_section(row, nbr_section, self.specific_config.sections_txt,
                                                                lang)

                        self.setup_condition(row['condition'])

                        if row['answer_format'].lower() == 'one choice':
                            self.setup_question('one choice', row, txt_lang, lang)
                            self.setup_answer('one choice', row, index_lang, lang)

                        if row['answer_format'].lower() == 'ranking':
                            # Ranking questions work differently
                            # First a list of rank SQ class need to be created (max 8 here)
                            # Then only the questions are created
                            # As neither of them have specific value for database, they are
                            # created here and not pulled from the config file
                            self.setup_question('ranking', row, txt_lang, lang)
                            # Create the Subquestion ranks
                            self.setup_subquestion('ranking', lang)
                            self.setup_answer('ranking', row, index_lang, lang)

                        if row['answer_format'].lower() == 'multiple choices':
                            self.setup_question('multiple choice', row, txt_lang, lang)

                            self.setup_answer('multi choice', row, index_lang, lang)

                        if row['answer_format'].lower() == 'freenumeric':
                            self.setup_question('freenumeric', row, txt_lang, lang)

                        if row['answer_format'].lower() == 'freetext':
                            self.setup_question('freetext', row, txt_lang, lang)

                        if row['answer_format'].lower() == 'likert':
                            self.setup_question('likert', row, txt_lang, lang)
                            # Need to create an  empty subquestion
                            self.setup_subquestion('likert', lang)
                            self.setup_answer('likert', row, index_lang, lang)

                        if row['answer_format'].lower() == 'y/n/na':
                            self.setup_question('y/n/na', row, txt_lang, lang)

    def run(self):
        """
        Run the survey creation
        """
        self.outfile = self.init_outfile()
        self.create_header()
        self.languages = self._get_languages()
        self.create_survey_settings()
        self.create_survey_questions()


def main():
    # Get which survey
    folder = sys.argv[1]
    create_survey = surveyCreation(folder)
    create_survey.run()


if __name__ == "__main__":
    main()
