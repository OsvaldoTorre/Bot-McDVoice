import random
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (NoSuchElementException, 
                                      TimeoutException,
                                      StaleElementReferenceException)

# Configuración
URL = "https://www.mcdvoice.com"
QUESTION_DURATION = 10  # 30 segundos por pregunta
MAX_ATTEMPTS = 3  # Intentos máximos para encontrar elementos
TICKET_NUMBER = ["26108", "01130", "60525", "16266", "00380", "8"]  # Número de ticket completo

class McDVoiceSurvey:
    def __init__(self):
        self.driver = self._init_browser()
        self.wait = WebDriverWait(self.driver, 15)
        self.validation_code = None
        self.survey_completion_text = None
        
    def _init_browser(self):
        """Configura e inicia el navegador Firefox"""
        options = Options()
        options.add_argument("--start-maximized")
        options.set_preference("dom.webnotifications.enabled", False)
        options.set_preference("intl.accept_languages", "es-US")
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        
        # Headers para parecer más humano
        options.set_preference("general.useragent.override", 
                             "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0")
        
        driver = webdriver.Firefox(options=options)
        return driver
    
    def timed_delay(self, seconds):
        """Pausa exacta con temporizador visible"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=seconds)
        
        while datetime.now() < end_time:
            remaining = (end_time - datetime.now()).seconds
            print(f"\rTiempo restante en esta pregunta: {remaining} segundos", end="")
            time.sleep(1)
        print()  # Salto de línea al finalizar
    
    def find_element(self, by, value, attempts=MAX_ATTEMPTS):
        """Busca un elemento con múltiples intentos"""
        for _ in range(attempts):
            try:
                element = self.driver.find_element(by, value)
                if element.is_displayed() and element.is_enabled():
                    return element
            except (NoSuchElementException, StaleElementReferenceException):
                time.sleep(1)
        return None
    
    def safe_click(self, element):
        """Intenta hacer clic en un elemento de manera segura"""
        try:
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception:
            return False
    
    def enter_ticket_number(self):
        """Ingresa el número de ticket en los campos correspondientes"""
        try:
            print("\nIngresando número de ticket...")
            for i, part in enumerate(TICKET_NUMBER, start=1):
                field = self.find_element(By.ID, f"CN{i}")
                if field:
                    field.clear()
                    field.send_keys(part)
                    print(f"  Parte {i} del ticket ingresada: {part}")
                    self.timed_delay(3)  # 3 segundos entre cada campo
            
            next_btn = self.find_element(By.ID, "NextButton")
            if next_btn and self.safe_click(next_btn):
                print("Número de ticket completado, avanzando...")
                self.timed_delay(5)  # Espera después de enviar el ticket
                return True
        except Exception as e:
            print(f"Error ingresando ticket: {str(e)}")
        return False
    
    def answer_likelihood_questions(self):
        """Responde preguntas de tipo 'likelihood' (probabilidad) con escala de 5 puntos"""
        try:
            # Buscar todas las tablas de preguntas de probabilidad
            tables = self.driver.find_elements(By.XPATH, "//table[contains(@class, 'HighlyLikelyDESC')]")
            
            for table in tables:
                if table.is_displayed():
                    # Obtener el título de la sección
                    section_title = "Sección de probabilidad"
                    try:
                        caption = table.find_element(By.XPATH, ".//caption//h2")
                        section_title = caption.text.strip()
                    except:
                        pass
                    
                    print(f"\nProcesando sección: {section_title}")
                    
                    # Obtener todas las filas de preguntas
                    question_rows = table.find_elements(By.XPATH, ".//tbody//tr[contains(@id, 'FNSR')]")
                    
                    for row in question_rows:
                        if row.is_displayed():
                            # Obtener el texto de la pregunta
                            question_text = "Desconocida"
                            try:
                                question_element = row.find_element(By.XPATH, ".//th[@class='LeftColumn']")
                                question_text = question_element.text.strip()
                            except:
                                pass
                            
                            print(f"  Evaluando: {question_text}")
                            
                            # Determinar ponderación basada en el tipo de pregunta
                            if "recommend" in question_text.lower():
                                # Más probabilidad de respuestas positivas para recomendación
                                weights = [0.70, 0.20, 0.07, 0.02, 0.01]
                            elif "return" in question_text.lower():
                                # Probabilidad media para retorno
                                weights = [0.60, 0.25, 0.10, 0.04, 0.01]
                            else:
                                # Para otras preguntas de probabilidad
                                weights = [0.50, 0.30, 0.15, 0.04, 0.01]
                            
                            # Buscar todas las opciones de radio en la fila
                            options = row.find_elements(By.XPATH, ".//input[@type='radio']")
                            visible_options = [o for o in options if o.is_displayed()]
                            
                            if visible_options and len(weights) == len(visible_options):
                                selected_option = random.choices(visible_options, weights=weights, k=1)[0]
                                
                                # Hacer clic en la opción seleccionada
                                label = row.find_element(By.XPATH, f".//label[@for='{selected_option.get_attribute('id')}']")
                                
                                if self.safe_click(label):
                                    value = selected_option.get_attribute("value")
                                    rating_map = {
                                        "5": "Highly Likely",
                                        "4": "Likely",
                                        "3": "Somewhat Likely",
                                        "2": "Not Very Likely",
                                        "1": "Not At All Likely"
                                    }
                                    rating_text = rating_map.get(value, "Opción seleccionada")
                                    print(f"    Seleccionado: {rating_text}")
                                    self.timed_delay(2)  # Pequeña pausa entre preguntas
                    
                    # Espera el tiempo restante para completar los 30 segundos por grupo de preguntas
                    remaining_time = max(0, QUESTION_DURATION - (2 * len(question_rows)))
                    if remaining_time > 0:
                        self.timed_delay(remaining_time)
        except Exception as e:
            print(f"Error respondiendo preguntas de probabilidad: {str(e)}")

    def answer_dropdown_questions(self):
        """Responde preguntas de tipo dropdown (desplegables)"""
        try:
            # Buscar todos los elementos select visibles
            dropdowns = self.driver.find_elements(By.XPATH, "//select[not(contains(@class, 'hidden')) and not(@aria-hidden='true')]")
            
            for dropdown in dropdowns:
                if dropdown.is_displayed():
                    # Obtener la pregunta asociada al dropdown
                    question_text = "Pregunta dropdown"
                    try:
                        label = self.driver.find_element(By.XPATH, f"//label[@for='{dropdown.get_attribute('id')}']")
                        question_text = label.text.strip()
                    except:
                        pass
                    
                    print(f"\nProcesando pregunta dropdown: {question_text}")
                    
                    # Crear objeto Select para manipular el dropdown
                    select = Select(dropdown)
                    options = select.options
                    
                    # Filtrar opciones válidas excluyendo placeholders y opciones de no respuesta
                    valid_options = [
                        opt for opt in options 
                        if opt.get_attribute('value') 
                        and opt.text.strip() not in [" - Select One - ", "Prefer not to answer", "No deseo responder", "Prefiero no contestar"]
                        and not opt.text.strip().startswith(" - ")
                        and opt.text.strip() != ""
                    ]
                    
                    if valid_options:
                        # Selección completamente aleatoria sin ponderaciones
                        selected = random.choice(valid_options)
                        
                        # Seleccionar la opción
                        select.select_by_value(selected.get_attribute('value'))
                        print(f"  Seleccionado aleatoriamente: {selected.text}")
                        
                        self.timed_delay(2)  # Pequeña pausa después de seleccionar
                    else:
                        print("  No se encontraron opciones válidas para seleccionar")
                        
        except Exception as e:
            print(f"Error respondiendo preguntas dropdown: {str(e)}")

    def answer_scale_questions(self):
        """Responde preguntas con escala de satisfacción"""
        try:
            tables = self.driver.find_elements(By.XPATH, "//table[contains(@class, 'HighlySatisfiedNeitherDESC')]")
            
            for table in tables:
                if table.is_displayed():
                    section_title = "Sección de satisfacción"
                    try:
                        caption = table.find_element(By.XPATH, ".//caption//h2")
                        section_title = caption.text.strip()
                    except:
                        pass
                    
                    print(f"\nProcesando sección: {section_title}")
                    
                    question_rows = table.find_elements(By.XPATH, ".//tbody//tr[contains(@id, 'FNSR')]")
                    
                    for row in question_rows:
                        if row.is_displayed():
                            question_text = "Desconocida"
                            try:
                                question_element = row.find_element(By.XPATH, ".//th[@class='LeftColumn']")
                                question_text = question_element.text.strip()
                            except:
                                pass
                            
                            print(f"  Evaluando: {question_text}")
                            
                            if "shake" in question_text.lower():
                                weights = [0.70, 0.20, 0.07, 0.02, 0.01]
                            elif "mcflurry" in question_text.lower() or "cone" in question_text.lower():
                                weights = [0.65, 0.25, 0.07, 0.02, 0.01]
                            elif "breakfast" in question_text.lower() or "bagel" in question_text.lower() or "muffin" in question_text.lower():
                                weights = [0.50, 0.30, 0.15, 0.04, 0.01]
                            else:
                                weights = [0.60, 0.25, 0.10, 0.04, 0.01]
                            
                            options = row.find_elements(By.XPATH, ".//input[@type='radio']")
                            visible_options = [o for o in options if o.is_displayed()]
                            
                            if visible_options and len(weights) == len(visible_options):
                                selected_option = random.choices(visible_options, weights=weights, k=1)[0]
                                label = row.find_element(By.XPATH, f".//label[@for='{selected_option.get_attribute('id')}']")
                                
                                if self.safe_click(label):
                                    value = selected_option.get_attribute("value")
                                    rating_map = {
                                        "5": "Highly Satisfied",
                                        "4": "Satisfied",
                                        "3": "Neutral",
                                        "2": "Dissatisfied",
                                        "1": "Highly Dissatisfied"
                                    }
                                    rating_text = rating_map.get(value, "Opción seleccionada")
                                    print(f"    Seleccionado: {rating_text}")
                                    self.timed_delay(2)
                    
                    remaining_time = max(0, QUESTION_DURATION - (2 * len(question_rows)))
                    if remaining_time > 0:
                        self.timed_delay(remaining_time)
        except Exception as e:
            print(f"Error respondiendo preguntas de escala: {str(e)}")
    
    def answer_problem_experience_questions(self):
        """Responde preguntas sobre problemas experimentados"""
        try:
            fieldsets = self.driver.find_elements(By.XPATH, """
                //fieldset[contains(@class, 'inputtypeopt') 
                and .//legend[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'problem you experienced')]]""")
            
            for fieldset in fieldsets:
                if fieldset.is_displayed():
                    question_text = "Desconocida"
                    try:
                        legend = fieldset.find_element(By.XPATH, ".//legend")
                        question_text = legend.text.strip()
                    except:
                        pass
                    
                    print(f"\nProcesando pregunta sobre problemas: {question_text[:100]}...")
                    
                    options = fieldset.find_elements(By.XPATH, ".//div[contains(@class, 'cataOption')]")
                    selected_options = []
                    
                    serious_problem = random.choices([True, False], weights=[0.2, 0.8], k=1)[0]
                    
                    if serious_problem:
                        print("  Simulando un problema serio - seleccionando múltiples opciones")
                        common_problems = [
                            "Accuracy of order",
                            "Quality of food",
                            "Speed of service",
                            "cleanliness",
                            "Product availability"
                        ]
                        
                        num_problems = random.randint(2, min(4, len(options)))
                        selected_indices = []
                        
                        for i, option in enumerate(options):
                            label = option.find_element(By.XPATH, ".//label")
                            label_text = label.text.lower()
                            if any(problem.lower() in label_text for problem in common_problems):
                                selected_indices.append(i)
                                if len(selected_indices) >= num_problems:
                                    break
                        
                        while len(selected_indices) < num_problems:
                            idx = random.choice([i for i in range(len(options)) if i not in selected_indices])
                            selected_indices.append(idx)
                        
                        for idx in selected_indices:
                            option = options[idx]
                            checkbox = option.find_element(By.XPATH, ".//input[@type='checkbox']")
                            label = option.find_element(By.XPATH, ".//label")
                            
                            if self.safe_click(checkbox):
                                option_text = label.text.strip()
                                selected_options.append(option_text)
                                print(f"  Reportando problema: {option_text}")
                                self.timed_delay(2)
                        
                        other_option = fieldset.find_elements(By.XPATH, ".//label[contains(., 'Other')]")
                        if other_option and other_option[0].is_displayed():
                            other_text = random.choice([
                                "Employee was rude",
                                "Wrong order twice",
                                "Food was cold",
                                "Long waiting time",
                                "Dirty tables"
                            ])
                            other_input = fieldset.find_element(By.XPATH, ".//input[@type='text']")
                            if other_input.is_displayed() and other_input.is_enabled():
                                other_input.send_keys(other_text)
                                print(f"  Detalle adicional: {other_text}")
                                self.timed_delay(3)
                    else:
                        print("  Simulando problema menor - seleccionando 1 opción")
                        minor_problems = [
                            "Friendliness of employees",
                            "Speed of service",
                            "cleanliness"
                        ]
                        
                        selected = False
                        for option in options:
                            label = option.find_element(By.XPATH, ".//label")
                            label_text = label.text.lower()
                            if any(problem.lower() in label_text for problem in minor_problems):
                                checkbox = option.find_element(By.XPATH, ".//input[@type='checkbox']")
                                if self.safe_click(checkbox):
                                    option_text = label.text.strip()
                                    selected_options.append(option_text)
                                    print(f"  Reportando problema menor: {option_text}")
                                    selected = True
                                    self.timed_delay(2)
                                    break
                        
                        if not selected and options:
                            option = random.choice(options)
                            checkbox = option.find_element(By.XPATH, ".//input[@type='checkbox']")
                            label = option.find_element(By.XPATH, ".//label")
                            if self.safe_click(checkbox):
                                option_text = label.text.strip()
                                selected_options.append(option_text)
                                print(f"  Reportando problema aleatorio: {option_text}")
                                self.timed_delay(2)
                    
                    print(f"  Problemas reportados: {', '.join(selected_options)}")
                    
                    remaining_time = max(0, QUESTION_DURATION - (2 * len(selected_options)))
                    if remaining_time > 0:
                        self.timed_delay(remaining_time)
        except Exception as e:
            print(f"Error respondiendo preguntas sobre problemas: {str(e)}")
    
    def answer_na_satisfaction_questions(self):
        """Responde preguntas de satisfacción con opción N/A"""
        try:
            tables = self.driver.find_elements(By.XPATH, """
                //table[contains(@class, 'HighlySatisfiedNeitherDESC') 
                and .//th[contains(@id, 'HighlySatisfiedNeitherDESC9')]]""")
            
            for table in tables:
                if table.is_displayed():
                    question_text = "Desconocida"
                    try:
                        question_element = table.find_element(By.XPATH, ".//th[@class='LeftColumn']")
                        question_text = question_element.text.strip()
                    except:
                        pass
                    
                    print(f"\nProcesando pregunta con opción N/A: {question_text[:100]}...")
                    
                    reported_problem = random.choices([True, False], weights=[0.3, 0.7], k=1)[0]
                    
                    if reported_problem:
                        print("  Suponiendo que el problema fue reportado - evaluando satisfacción")
                        if "problem" in question_text.lower():
                            weights = [0.20, 0.30, 0.20, 0.15, 0.15, 0.00]
                        else:
                            weights = [0.50, 0.30, 0.10, 0.05, 0.05, 0.00]
                    else:
                        print("  Suponiendo que el problema NO fue reportado - seleccionando N/A")
                        weights = [0.00, 0.00, 0.00, 0.00, 0.00, 1.00]
                    
                    options = table.find_elements(By.XPATH, ".//input[@type='radio']")
                    visible_options = [o for o in options if o.is_displayed()]
                    
                    if visible_options and len(weights) == len(visible_options):
                        selected_option = random.choices(visible_options, weights=weights, k=1)[0]
                        label = table.find_element(By.XPATH, f".//label[@for='{selected_option.get_attribute('id')}']")
                        
                        if self.safe_click(label):
                            header_id = selected_option.get_attribute("aria-labelledby")
                            if header_id:
                                header = table.find_element(By.ID, header_id)
                                option_text = header.text if header else "Opción seleccionada"
                            else:
                                option_text = "Opción seleccionada"
                            
                            print(f"  Seleccionado: {option_text}")
                    
                    self.timed_delay(QUESTION_DURATION)
        except Exception as e:
            print(f"Error respondiendo preguntas con N/A: {str(e)}")
    
    def answer_satisfaction_scale_questions(self):
        """Responde preguntas de satisfacción con escala de 5 puntos (sin N/A)"""
        try:
            tables = self.driver.find_elements(By.XPATH, """
                //table[contains(@class, 'HighlySatisfiedNeitherDESC') 
                and not(.//th[contains(@id, 'HighlySatisfiedNeitherDESC9')])]""")
            
            for table in tables:
                if table.is_displayed():
                    question_text = "Desconocida"
                    try:
                        question_element = table.find_element(By.XPATH, ".//th[@class='LeftColumn']")
                        question_text = question_element.text.strip()
                    except:
                        pass
                    
                    print(f"\nProcesando pregunta de satisfacción: {question_text[:100]}...")
                    
                    options = table.find_elements(By.XPATH, ".//input[@type='radio']")
                    visible_options = [o for o in options if o.is_displayed()]
                    
                    if visible_options:
                        weights = [0.60, 0.25, 0.10, 0.04, 0.01]
                        selected_option = random.choices(visible_options, weights=weights, k=1)[0]
                        label = table.find_element(By.XPATH, f".//label[@for='{selected_option.get_attribute('id')}']")
                        
                        if self.safe_click(label):
                            header_id = selected_option.get_attribute("aria-labelledby")
                            if header_id:
                                header = table.find_element(By.ID, header_id)
                                option_text = header.text if header else "Opción seleccionada"
                            else:
                                option_text = "Opción seleccionada"
                            
                            print(f"  Seleccionado: {option_text}")
                    
                    self.timed_delay(QUESTION_DURATION)
        except Exception as e:
            print(f"Error respondiendo preguntas de satisfacción: {str(e)}")
    
    def answer_checkbox_questions(self):
        """Responde preguntas con checkboxes (selección múltiple)"""
        try:
            fieldsets = self.driver.find_elements(By.XPATH, "//fieldset[contains(@class, 'inputtypeopt')]")
            
            for fieldset in fieldsets:
                if fieldset.is_displayed():
                    question_text = "Desconocida"
                    try:
                        legend = fieldset.find_element(By.XPATH, ".//legend")
                        question_text = legend.text.strip()
                    except:
                        pass
                    
                    print(f"\nProcesando pregunta de selección múltiple: {question_text}")
                    
                    options = fieldset.find_elements(By.XPATH, ".//div[contains(@class, 'cataOption')]")
                    
                    if "bakery & sweet treats" in question_text.lower():
                        sweet_items = []
                        for option in options:
                            label = option.find_element(By.XPATH, ".//label")
                            sweet_items.append((option, label.text.strip()))
                        
                        common_sweets = ["McFlurry", "Sundae", "Shake", "Cone"]
                        selected = []
                        
                        matching_items = [item for item in sweet_items if any(sweet in item[1] for sweet in common_sweets)]
                        num_to_select = min(2, max(1, len(matching_items)))
                        
                        if matching_items:
                            selected_items = random.sample(matching_items, num_to_select)
                            for item in selected_items:
                                option, text = item
                                checkbox = option.find_element(By.XPATH, ".//input[@type='checkbox']")
                                if self.safe_click(checkbox):
                                    selected.append(text)
                                    print(f"  Seleccionado postre: {text}")
                                    self.timed_delay(2)
                        else:
                            num_to_select = random.randint(1, min(2, len(sweet_items)))
                            selected_indices = random.sample(range(len(sweet_items)), num_to_select)
                            for idx in selected_indices:
                                option, text = sweet_items[idx]
                                checkbox = option.find_element(By.XPATH, ".//input[@type='checkbox']")
                                if self.safe_click(checkbox):
                                    selected.append(text)
                                    print(f"  Seleccionado ítem: {text}")
                                    self.timed_delay(2)
                        
                        print(f"  Postres seleccionados: {', '.join(selected)}")
                    elif "breakfast items" in question_text.lower():
                        breakfast_items = []
                        for option in options:
                            label = option.find_element(By.XPATH, ".//label")
                            breakfast_items.append((option, label.text.strip()))
                        
                        common_items = ["Hotcakes", "Hashbrown", "Burrito", "McGriddle", "Biscuit"]
                        selected = []
                        
                        matching_items = [item for item in breakfast_items if any(common in item[1] for common in common_items)]
                        num_to_select = min(3, max(1, len(matching_items)))
                        
                        if matching_items:
                            selected_items = random.sample(matching_items, num_to_select)
                            for item in selected_items:
                                option, text = item
                                checkbox = option.find_element(By.XPATH, ".//input[@type='checkbox']")
                                if self.safe_click(checkbox):
                                    selected.append(text)
                                    print(f"  Seleccionado ítem de desayuno: {text}")
                                    self.timed_delay(2)
                        else:
                            num_to_select = random.randint(1, min(3, len(breakfast_items)))
                            selected_indices = random.sample(range(len(breakfast_items)), num_to_select)
                            for idx in selected_indices:
                                option, text = breakfast_items[idx]
                                checkbox = option.find_element(By.XPATH, ".//input[@type='checkbox']")
                                if self.safe_click(checkbox):
                                    selected.append(text)
                                    print(f"  Seleccionado ítem: {text}")
                                    self.timed_delay(2)
                        
                        print(f"  Ítems de desayuno seleccionados: {', '.join(selected)}")
                    else:
                        selected_options = []
                        num_to_select = random.randint(1, min(3, len(options)))
                        selected_indices = random.sample(range(len(options)), num_to_select)
                        
                        for idx in selected_indices:
                            option = options[idx]
                            checkbox = option.find_element(By.XPATH, ".//input[@type='checkbox']")
                            label = option.find_element(By.XPATH, ".//label")
                            
                            if self.safe_click(checkbox):
                                option_text = label.text.strip()
                                selected_options.append(option_text)
                                print(f"  Seleccionada opción: {option_text}")
                                self.timed_delay(2)
                        
                        print(f"  Opciones seleccionadas: {', '.join(selected_options)}")
                    
                    remaining_time = max(0, QUESTION_DURATION - (2 * len(selected)))
                    if remaining_time > 0:
                        self.timed_delay(remaining_time)
        except Exception as e:
            print(f"Error respondiendo preguntas de checkbox: {str(e)}")
    
    def answer_table_questions(self):
        """Responde preguntas en formato de tabla simple (como Sí/No)"""
        try:
            tables = self.driver.find_elements(By.XPATH, """
                //table[contains(@class, 'Inputtyperbl') 
                and not(contains(@class, 'HighlySatisfiedNeitherDESC'))]""")
            
            for table in tables:
                if table.is_displayed():
                    question_text = "Desconocida"
                    try:
                        question_element = table.find_element(By.XPATH, ".//th[@class='LeftColumn']")
                        question_text = question_element.text.strip()
                    except:
                        pass
                    
                    print(f"\nProcesando pregunta en tabla: {question_text}")
                    
                    options = table.find_elements(By.XPATH, ".//input[@type='radio']")
                    visible_options = [o for o in options if o.is_displayed()]
                    
                    if visible_options:
                        option = random.choice(visible_options)
                        label = table.find_element(By.XPATH, f".//label[@for='{option.get_attribute('id')}']")
                        
                        if self.safe_click(label):
                            header_id = option.get_attribute("aria-labelledby")
                            if header_id:
                                header = table.find_element(By.ID, header_id)
                                option_text = header.text if header else "Opción seleccionada"
                            else:
                                option_text = "Opción seleccionada"
                            
                            print(f"  Seleccionada opción: {option_text}")
                            
                            self.timed_delay(QUESTION_DURATION)
        except Exception as e:
            print(f"Error respondiendo preguntas en tabla: {str(e)}")
    
    def answer_radio_questions(self):
        """Responde preguntas de radio button estándar"""
        try:
            fieldsets = self.driver.find_elements(By.XPATH, """
                //fieldset[contains(@class, 'inputtyperblv') 
                and not(ancestor::table) 
                and not(contains(@class, 'inputtypeopt'))]""")
            
            for i, fieldset in enumerate(fieldsets, 1):
                if fieldset.is_displayed():
                    question_text = "Desconocida"
                    try:
                        legend = fieldset.find_element(By.XPATH, ".//legend")
                        question_text = legend.text.strip()
                    except:
                        pass
                    
                    print(f"\nProcesando pregunta {i}: {question_text}")
                    
                    options = fieldset.find_elements(By.XPATH, ".//input[@type='radio' and @name]")
                    visible_options = [o for o in options if o.is_displayed()]
                    
                    if visible_options:
                        option = random.choice(visible_options)
                        label = self.driver.find_element(By.XPATH, f"//label[@for='{option.get_attribute('id')}']")
                        
                        if self.safe_click(label):
                            option_text = label.text.strip()
                            print(f"  Seleccionada opción: {option_text}")
                            
                            self.timed_delay(QUESTION_DURATION)
        except Exception as e:
            print(f"Error respondiendo preguntas estándar: {str(e)}")
    

    
    def get_survey_results(self):
        """Captura el código de validación y texto de finalización"""
        try:
            self.wait.until(EC.presence_of_element_located((By.ID, "finishIncentiveHolder")))
            
            val_code_element = self.find_element(By.XPATH, "//p[contains(@class, 'ValCode')]")
            if val_code_element:
                self.validation_code = val_code_element.text.replace("Validation Code: ", "").strip()
            
            thank_you_element = self.find_element(By.XPATH, "//p[@class='FinishHeader']")
            if thank_you_element:
                self.survey_completion_text = thank_you_element.text.strip()
            
            if not self.survey_completion_text:
                thank_you_alt = self.find_element(By.XPATH, "//h2//p[contains(text(), 'Thank you')]")
                if thank_you_alt:
                    self.survey_completion_text = thank_you_alt.text.strip()
            
            return True
        except Exception as e:
            print(f"Error obteniendo resultados: {str(e)}")
            return False
    
    def submit_page(self):
        """Envía la página actual y maneja posibles errores"""
        try:
            next_btn = self.find_element(By.XPATH, "//input[@type='submit' and contains(@value, 'Next')]") or \
                      self.find_element(By.ID, "NextButton")
            
            if next_btn and self.safe_click(next_btn):
                print("\nAvanzando a la siguiente página...")
                self.timed_delay(5)
                return True
            
            if self.check_survey_completion():
                self.get_survey_results()
                return False
            
            print("No se encontró botón siguiente válido")
            return False
        except Exception as e:
            print(f"Error enviando página: {str(e)}")
            return False
    
    def check_survey_completion(self):
        """Verifica si la encuesta ha sido completada"""
        try:
            completion_elements = self.driver.find_elements(By.XPATH, 
                "//*[contains(text(), 'Thank you') or contains(text(), 'Gracias') or contains(@id, 'finishIncentiveHolder')]")
            return len(completion_elements) > 0
        except Exception:
            return False
    
    def check_for_errors(self):
        """Verifica si hay mensajes de error en la página"""
        try:
            errors = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'error') or contains(@class, 'error')]")
            if errors:
                print("Se detectaron errores en la página")
                return True
        except Exception:
            pass
        return False
    
    def handle_session_timeout(self):
        """Maneja el diálogo de timeout de sesión si aparece"""
        try:
            timeout_dialog = self.find_element(By.XPATH, "//div[contains(@class, 'sessionTimeoutDialog')]")
            if timeout_dialog and timeout_dialog.is_displayed():
                extend_btn = self.find_element(By.XPATH, "//button[contains(text(), 'Extend Session')]")
                if extend_btn:
                    self.safe_click(extend_btn)
                    print("Sesión extendida")
                    self.timed_delay(5)
                    return True
        except Exception:
            pass
        return False
    
    def answer_open_text_questions(self):
        """Responde preguntas abiertas en campos textarea escribiendo letra por letra, simulando escritura humana."""
        try:
            textareas = self.driver.find_elements(By.XPATH, "//textarea[not(@disabled) and not(contains(@class, 'hidden'))]")
            respuestas = [
                "Me encantó la atención del personal, fueron muy amables.",
                "La comida estuvo deliciosa y el local muy limpio.",
                "El servicio fue rápido y eficiente, volveré pronto.",
                "Todo estuvo perfecto, muchas gracias.",
                "Excelente experiencia, felicidades al equipo."
            ]
            for textarea in textareas:
                if textarea.is_displayed() and textarea.is_enabled():
                    comentario = random.choice(respuestas)
                    textarea.clear()
                    for letra in comentario:
                        textarea.send_keys(letra)
                        time.sleep(random.uniform(0.05, 0.15))  # Pausa aleatoria entre letras
                    print(f"  Comentario abierto ingresado: {comentario}")
                    self.timed_delay(5)
        except Exception as e:
            print(f"Error respondiendo pregunta abierta: {str(e)}")

    def answer_overall_satisfaction_highly_satisfied(self):
        """
        Responde la pregunta 'Please rate your overall satisfaction...' seleccionando siempre 'Highly Satisfied'.
        """
        try:
            # Busca la tabla con la clase HighlySatisfiedNeitherDESC
            tables = self.driver.find_elements(By.XPATH, "//table[contains(@class, 'HighlySatisfiedNeitherDESC')]")
            for table in tables:
                if table.is_displayed():
                    # Busca la fila con la pregunta específica
                    rows = table.find_elements(By.XPATH, ".//tr[contains(@id, 'FNSR')]")
                    for row in rows:
                        if row.is_displayed():
                            question_element = row.find_element(By.XPATH, ".//th[@class='LeftColumn']")
                            question_text = question_element.text.strip().lower()
                            if "overall satisfaction" in question_text:
                                # Selecciona el radio con value='5' (Highly Satisfied)
                                option = row.find_element(By.XPATH, ".//input[@type='radio' and @value='5']")
                                label = row.find_element(By.XPATH, f".//label[@for='{option.get_attribute('id')}']")
                                if self.safe_click(label):
                                    print("  Seleccionado: Highly Satisfied")
                                    self.timed_delay(2)
                                return  # Solo responde esta pregunta
        except Exception as e:
            print(f"Error respondiendo pregunta de satisfacción general: {str(e)}")

    def run_survey(self):
        """Ejecuta el proceso completo de la encuesta"""
        try:
            print("="*50)
            print("INICIANDO ENCUESTA MCDVOICE")
            print(f"Configuración: {QUESTION_DURATION} segundos por pregunta")
            print("="*50 + "\n")
            
            print("Cargando página inicial...")
            self.driver.get(URL)
            self.timed_delay(5)
            
            self.wait.until(EC.presence_of_element_located((By.ID, "CN1")))
            
            if not self.enter_ticket_number():
                print("Fallo al ingresar número de ticket")
                return
            
            while True:
                self.handle_session_timeout()
                
                # Manejar preguntas de probabilidad específicamente
                likelihood_tables = self.driver.find_elements(By.XPATH, "//table[contains(@class, 'HighlyLikelyDESC')]")
                if likelihood_tables:
                    self.answer_likelihood_questions()
                    if not self.submit_page():
                        break
                    continue

                
                self.answer_open_text_questions()        # 1. Responde preguntas abiertas tipo textarea
                self.answer_dropdown_questions()         # 2. Responde dropdowns/demográficos (suelen estar al inicio)
                self.answer_radio_questions()            # 3. Preguntas de radio estándar (simples, suelen aparecer antes)
                self.answer_table_questions()            # 4. Preguntas tipo tabla (Sí/No, suelen ser directas)
                self.answer_checkbox_questions()         # 5. Selección múltiple (checkboxes, suelen estar después)
                self.answer_problem_experience_questions() # 6. Problemas experimentados (aparecen tras preguntas generales)
                self.answer_na_satisfaction_questions()  # 7. Satisfacción con opción N/A (depende de problemas reportados)
                self.answer_satisfaction_scale_questions() # 8. Satisfacción escala sin N/A
                self.answer_scale_questions()            # 9. Satisfacción escala (general)
                self.answer_overall_satisfaction_highly_satisfied() # 10. Satisfacción general (si aplica)

                if self.check_for_errors():
                    break

                if not self.submit_page():
                    break

            if self.validation_code or self.survey_completion_text:
                print("\n" + "="*50)
                print("ENCUESTA COMPLETADA CON ÉXITO")
                print("="*50)
                if self.validation_code:
                    print(f"Código de Validación: {self.validation_code}")
                if self.survey_completion_text:
                    print(f"Mensaje: {self.survey_completion_text}")
                print("="*50 + "\n")
                
        except TimeoutException:
            print("Tiempo de espera agotado - La página no cargó correctamente")
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
        finally:
            print("Finalizando sesión del navegador...")
            self.timed_delay(3)
            self.driver.quit()

    def run_survey_general_satisfaction(self):
        """Ejecuta solo la pregunta de satisfacción general"""
        try:
            print("="*50)
            print("INICIANDO ENCUESTA MCDVOICE (Solo satisfacción general)")
            print("="*50 + "\n")
            
            print("Cargando página inicial...")
            self.driver.get(URL)
            self.timed_delay(5)
            
            self.wait.until(EC.presence_of_element_located((By.ID, "CN1")))
            
            if not self.enter_ticket_number():
                print("Fallo al ingresar número de ticket")
                return
            
            self.answer_overall_satisfaction_highly_satisfied()
            self.submit_page()

        except TimeoutException:
            print("Tiempo de espera agotado - La página no cargó correctamente")
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
        finally:
            print("Finalizando sesión del navegador...")
            self.timed_delay(3)
            self.driver.quit()

if __name__ == "__main__":
    survey = McDVoiceSurvey()
    survey.run_survey()

