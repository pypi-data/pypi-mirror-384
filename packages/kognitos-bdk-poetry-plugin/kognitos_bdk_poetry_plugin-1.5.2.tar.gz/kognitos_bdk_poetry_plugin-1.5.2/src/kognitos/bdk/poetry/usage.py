import json
import re
import tempfile
from operator import itemgetter
from typing import Any, Dict, List, Optional, Union

from cleo.helpers import option
from poetry.console.commands.command import Command
from poetry.utils.env import EnvManager
from rich.console import Console
from snakemd import Document

console = Console()
BOOK_CONCEPT_LIST = ["ConceptOpaqueType", "ConceptDictionaryType", "ConceptListType"]
CONCEPTS_WITH_MULTIPLE_INNER_TYPES = ["ConceptUnionType"]


class UsageCommand(Command):
    name = "bdk usage"
    description = "Generate USAGE.md for all the books contained in this project"

    options = [
        option("force", "f", "Overwrite the current USAGE.md file", flag=True),
    ]

    def handle(self) -> int:
        books = self.poetry.pyproject.data.get("tool", {}).get("poetry", {}).get("plugins", {}).get("kognitos-book", {})

        console.log("[bold blue]Loading up virtual environment...[/bold blue]")
        env = EnvManager(self.poetry).get()
        console.log(f"[bold blue]Virtual Environment: [/bold blue][bold green]{env.path}[/bold green]")
        master_document = Document()

        if len(books) > 1:
            self.__generate_multiple_books_documentation(books, env, master_document)
        else:
            self.__generate_single_book_documentation(books, env, master_document)

        console.log("[bold blue]Done[/bold blue]")
        return 0

    def __generate_multiple_books_documentation(self, books: Dict, env, master_document: Document) -> None:
        """
        Generate documentation for multiple books.

        Args:
            books (Dict): Dictionary of book entries.
            env: The virtual environment.
            master_document (Document): The master document object.

        Returns:
            List[Dict]: List of book documentation details.
        """
        doc_list = []
        for _, book_entry in books.items():
            book_name = self.__generate_book_documentation(book_entry, env=env, multiple_book=True)
            doc_list.append(
                {"title": str(book_name).capitalize(), "filename": f"USAGE.{str(book_name).capitalize()}.md"},
            )
        master_document.add_heading("Book Reference", 2)
        for doc in doc_list:
            master_document.add_paragraph(f"- [{doc['title']}]({doc['filename']})")
        master_document.dump("USAGE")

    def __generate_single_book_documentation(self, books: Dict, env, master_document: Document) -> None:
        """
        Generate documentation for a single book.

        Args:
            books (Dict): Dictionary of book entries.
            env: The virtual environment.
            master_document (Document): The master document object.
        """
        for _, book_entry in books.items():
            self.__generate_book_documentation(book_entry, env=env, usage_document=master_document)

    def __generate_book_documentation(
        self, book_entry, env, multiple_book: bool = False, usage_document: Union[Document, None] = None
    ):
        """
        Generate documentation for a specific book.

        Args:
            book_entry (str): The book entry string.
            env: The virtual environment.
            multiple_book (bool): Flag to generate a new document.
            usage_document (Optional[Document]): The usage document object.

        Returns:
            str: The name of the book.
        """
        module_name, class_name = book_entry.split(":")
        console.log(f"[bold blue]Trying to obtain metadata for {book_entry}[/bold blue]")

        if not usage_document and multiple_book:
            book_document = Document()
        else:
            book_document = usage_document

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            console.log("[bold blue]Generating metadata inside virtual environment[/bold blue]")
            console.log(f"[bold blue]Temporary File: [/bold blue][bold green]{tmp.name}[/bold green]")
            env.run_python_script(
                f"""
from {module_name} import {class_name}
import json
import inspect

class BookEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_json"):
            return self.default(obj.to_json())
        elif hasattr(obj, "__dict__"):
            d = {{
                "class_name": obj.__class__.__name__,
                **{{
                    key: value
                    for key, value in inspect.getmembers(obj)
                    if not key.startswith("_")
                    and not inspect.isabstract(value)
                    and not inspect.isbuiltin(value)
                    and not inspect.isfunction(value)
                    and not inspect.isgenerator(value)
                    and not inspect.isgetsetdescriptor(value)
                    and not inspect.isgeneratorfunction(value)
                    and not inspect.ismethod(value)
                    and not inspect.ismethoddescriptor(value)
                    and not inspect.isroutine(value)
                }},
            }}
            return d
        elif isinstance(obj, bytes):
            return obj.decode("utf-8")
        return None

with open("{tmp.name}", "w", encoding="utf-8") as f:
    json.dump({class_name}.__book__, f, cls=BookEncoder, sort_keys=True, indent=4)"""
            )

        with open(tmp.name, "r", encoding="utf-8") as file:
            console.log("[bold blue]Reading generated metadata from virtual environment[/bold blue]")
            book_metadata = json.load(file)

            console.log("[bold blue]Generating usage documentation[/bold blue]")
            book_metadata["module_name"] = module_name
            book_metadata["multiple_book"] = multiple_book
            self.generate_usage(book_document, class_name, book_metadata)

        book_name = book_metadata.get("name", None)
        if not book_name:
            book_name = class_name
        book_name = book_name.replace(" ", "")
        console.log(f"[bold blue]Generated usage documentation for {book_name} [/bold blue]")
        if multiple_book:
            book_document.dump(f"USAGE.{str(book_name).upper()}")  # type: ignore
        else:
            book_document.dump("USAGE")  # type: ignore

        return book_name

    def generate_usage(self, usage_document, book_class_name: str, book_metadata):
        book_name = book_metadata.get("name", None)
        if not book_name:
            book_name = book_class_name
        self.__add_book_logo(usage_document, book_metadata)
        self.__add_book_reference_title(usage_document, book_name)
        self.__add_book_description(usage_document, book_metadata)
        usage_document.add_table_of_contents(range(2, 4))
        self.__add_book_connectivity(usage_document, book_metadata)
        self.__add_book_configuration(usage_document, book_name, book_metadata)
        self.__add_book_procedures(usage_document, book_metadata)
        self.__add_book_concepts(usage_document, book_metadata)

    def __add_book_connectivity(self, usage_document, book_metadata):
        def format_labels(labels: Optional[List[Any]]) -> str:
            if labels and len(labels) > 1:
                return ", ".join(labels[:-1]) + " and " + labels[-1]

            if labels:
                return labels[0]

            return ""

        book_authentications = book_metadata.get("authentications", [])

        if book_authentications:
            console.log("[bold blue]Generating connectivity information[/bold blue]")

            usage_document.add_heading("Connectivity", 2)

            usage_document.add_paragraph(
                "This books supports the connectivity methods described in this section."
                "In here you will find information about what information is required in order to employ each method."
            )

            for auth in book_authentications:
                credentials = auth.get("credentials", None)

                if credentials:
                    labels = [credential.get("label", None) for credential in credentials]
                    description = auth.get("description", None)
                    usage_document.add_heading(f"Connect using {format_labels(labels)}", 3)

                    if description:
                        usage_document.add_paragraph(description)

                    self.__add_credentials_table(usage_document, credentials)

    def __add_book_configuration(self, usage_document, book_name, book_metadata):
        book_configurations = book_metadata.get("configuration", [])

        if book_configurations:
            console.log("[bold blue]Generating configuration information[/bold blue]")

            concepts = [book_config.get("concept", {}) for book_config in book_configurations]

            usage_document.add_heading("Configuration", 2)

            usage_document.add_paragraph(
                "The following table details all the available configuration options for this book."
            )

            self.__add_concept_table(usage_document, concepts, include_required=False)

            # find the first config element with a default value
            example_concepts = [concept for concept in concepts if concept.get("default_value", None)]

            usage_document.add_paragraph("Configuration can be set or retrieved as shown in the following examples:")

            for example_concept in example_concepts:
                noun_phrases_str = (
                    "'s ".join(
                        [
                            " ".join((noun_phrase.get("modifiers", [])) + [noun_phrase.get("head")])
                            for noun_phrase in example_concept.get("noun_phrases")
                        ]
                    )
                    if example_concept.get("noun_phrases", None)
                    else ""
                )
                usage_document.add_code(
                    f"the department's {book_name}'s {noun_phrases_str} is {example_concept.get('default_value', None)}"
                )

    def __add_book_procedures(self, usage_document, book_metadata):
        book_procedures = book_metadata.get("procedures", [])
        if book_procedures:
            usage_document.add_heading("Procedures", 2)

        sorted_procedures = sorted(book_procedures, key=lambda x: x["english_signature"].get("english"))
        for book_procedure in sorted_procedures:
            english_signature = book_procedure.get("english_signature", {})

            english_signature_text = english_signature.get("english", None)

            console.log(f"[bold blue]Documenting: [/bold blue][bold green]{english_signature_text}[/bold green]")

            if english_signature_text:
                usage_document.add_heading(english_signature_text, 3)
                usage_document.add_horizontal_rule()

            if book_procedure.get("filter_capable"):
                badge_link = (
                    "![FILTER - CAPABLE](https://img.shields.io/static/v1?label=FILTER&message=CAPABLE&color=blue)"
                )
                usage_document.add_raw(badge_link)

            short_description = book_procedure.get("short_description", None)
            long_description = book_procedure.get("long_description", None)

            if short_description:
                usage_document.add_paragraph(short_description)

            if long_description:
                usage_document.add_paragraph(long_description)

            input_concepts = book_procedure.get("input_concepts", None)
            if input_concepts:
                usage_document.add_heading("Input Concepts", 4)
                self.__add_concept_table(usage_document, input_concepts)

            output_concepts = book_procedure.get("output_concepts", None)
            if output_concepts:
                usage_document.add_heading("Output Concepts", 4)
                self.__add_concept_table(usage_document, output_concepts, include_required=False, include_default=False)

            question_descriptions = book_procedure.get("questions", None)
            if question_descriptions:
                usage_document.add_heading("Questions", 4)
                self.add_question_table(usage_document, question_descriptions)

            book_procedure_examples = book_procedure.get("examples", None)

            if book_procedure_examples:
                usage_document.add_heading("Examples", 4)
                self.add_examples(usage_document, book_procedure_examples)

    def add_examples(self, usage_document, examples):
        for example in examples:
            example_description = example.get("description", None)
            example_snippet = example.get("snippet", None)

            if example_description:
                usage_document.add_paragraph(example_description)

            if example_snippet:
                usage_document.add_code(example_snippet)

    def __add_book_description(self, usage_document, book_metadata):
        book_short_description = book_metadata.get("short_description", None)
        book_long_description = book_metadata.get("long_description", None)
        if book_short_description:
            usage_document.add_paragraph(book_short_description)
        if book_long_description:
            usage_document.add_paragraph(book_long_description)

    def __add_book_reference_title(self, usage_document, book_name):
        usage_document.add_heading(f"{book_name} Reference", 1)

    @staticmethod
    def refactor_names(name: str, link: bool = False, raw: bool = False) -> Union[str, List[str]]:
        words = [word.replace("`", "").strip() for word in name.lower().split(" or ")]
        words.sort()
        if raw:
            return words
        if link:
            words = [word.replace("`", "") for word in words]
            return words[0].replace(" ", "-")
        return " or ".join([f"`{word}`" for word in words])

    @staticmethod
    def get_concept_type(concept_data: Dict) -> Dict:
        concept_class_type = concept_data.get("type", {})
        if concept_class_type.get("type"):
            return UsageCommand.get_concept_type(concept_class_type)

        return concept_class_type

    @staticmethod
    def get_concept_inner_types(concept_data: Dict) -> List[Dict]:
        return concept_data.get("inners", [])

    @staticmethod
    def check_list_type(concept_data: Dict) -> bool:
        if concept_data.get("class_name") == "ConceptListType":
            return True
        concept_class_type = concept_data.get("type", {})
        if concept_class_type.get("type"):
            return UsageCommand.check_list_type(concept_class_type)
        return False

    def __add_book_logo(self, usage_document, book_metadata):
        icon_path = book_metadata.get("icon_path", "")
        icon = icon_path.split("/src")[-1] if icon_path else "data/icon.svg"
        usage_document.add_raw(f'<img src="src/{icon}" width="128" height="128">')

    def __format_noun_phrases(self, noun_phrases):
        """Format noun phrases by concatenating modifiers and head with 's separator."""
        return (
            "'s ".join(
                [
                    " ".join(
                        (noun_phrase.get("modifiers", []) if noun_phrase.get("modifiers", None) else [])
                        + [noun_phrase.get("head")]
                    )
                    for noun_phrase in noun_phrases
                ]
            )
            if noun_phrases
            else ""
        )

    def __add_concept_table(self, usage_document, concepts, include_required=True, include_default=True):
        headers = ["Concept", "Description", "Type"]

        if include_required:
            headers.append("Required")

        if include_default:
            headers.append("Default Value")

        rows = []
        for concept in concepts:
            noun_phrases = concept.get("noun_phrases", None)
            concept_type = self.get_concept_type(concept)
            description = concept.get("description", None)
            is_optional = concept.get("is_optional", None)
            default_value = concept.get("default_value", None)

            if isinstance(default_value, dict) and default_value.get("head", None):
                default_value = " ".join(
                    (default_value.get("modifiers", []) if default_value.get("modifiers", None) else [])
                    + [default_value.get("head")]
                )

            concept_type_name = concept_type.get("name", "")

            if concept_type_name.lower() == "conceptual":
                concept_type_name = "noun"

            noun_phrases_str = self.__format_noun_phrases(noun_phrases)

            if concept_type.get("class_name") in BOOK_CONCEPT_LIST:
                row_concept_name = f"[`{noun_phrases_str}`](#{self.refactor_names(concept_type_name, link=True)})"
            else:
                row_concept_name = f"`{noun_phrases_str}`"

            if self._is_plain_dict(concept_type.get("class_name", ""), concept_type):
                row_concept_name = f"`{noun_phrases_str}`"
                concept_type_name = "json"

            row = [
                row_concept_name,
                description,
                self.refactor_names(concept_type_name),
            ]

            if include_required:
                row.append("No" if is_optional else "Yes")

            if include_default:
                row.append(default_value if default_value is not None else "(no default)")

            rows.append(row)

        usage_document.add_table(header=headers, data=rows)

    def add_question_table(self, usage_document, question_descriptions):
        headers = ["Noun phrases", "Type"]
        rows = []

        for question_description in question_descriptions:
            noun_phrases = question_description.get("noun_phrases", {}).get("noun_phrases", [])
            concept_type = self.get_concept_type(question_description)
            concept_type_name = concept_type.get("name", "")

            noun_phrases_str = self.__format_noun_phrases(noun_phrases)

            concept_type_formatted = self.refactor_names(concept_type_name)

            rows.append([f"`{noun_phrases_str}`", concept_type_formatted])

        usage_document.add_table(header=headers, data=rows)

    def __add_credentials_table(self, usage_document, credentials):
        headers = ["Label", "Description", "Type"]

        rows = []
        for credential in credentials:
            label = credential.get("label", None)
            credential_type = credential.get("type", None)
            description = credential.get("description", None)

            credential_type_name = credential_type.get("name", None)

            row = [
                label,
                description,
                f"`{credential_type_name.lower()}`",
            ]

            rows.append(row)

        usage_document.add_table(header=headers, data=rows)

    def __process_concept_fields(self, concept_type: Dict, schemas_to_add: Dict):
        if concept_type.get("class_name") != "ConceptDictionaryType":
            return None, []

        headers = ["Field Name", "Description", "Type"]
        rows = []

        for field in concept_type.get("fields", []):
            # Generate link or name for field
            field_name = field.get("name", "")
            field_type_info = field.get("t", {})
            class_name = field_type_info.get("class_name", "")
            field_link = field_type_info.get("name", "").lower().replace(" ", "-")

            # Generate field name as a link if it's in BOOK_CONCEPT_LIST
            if class_name in BOOK_CONCEPT_LIST:
                field_name = f"[`{field_name}`](#{field_link})"
            else:
                field_name = f"`{field_name}`"

            # Determine the field type, handling optional and nested concepts
            field_type = self.refactor_names(field_type_info.get("name", ""))
            is_optional = class_name == "ConceptOptionalType"
            inner_concept = self.get_concept_type(field_type_info)

            if self._is_plain_dict(class_name, field):
                field_name = f'`{field.get("name")}`'
                field_type = "json"

            # If there's an inner concept that’s in BOOK_CONCEPT_LIST, adjust name and type accordingly
            if inner_concept and inner_concept.get("class_name") in BOOK_CONCEPT_LIST:
                if self._is_plain_dict(inner_concept.get("class_name", ""), inner_concept):
                    field_name = f'`{field.get("name")}`'
                    field_type = "json"
                elif not inner_concept.get("name"):
                    inner_name = field.get("name")
                    schema_header = f'{inner_name} ({concept_type.get("name", "")})'
                    anchor = re.sub(r"[^\w\s-]", "", schema_header.lower()).replace(" ", "-")
                    field_name = f"[`{inner_name}`](#{anchor})"
                    field_type = "json"
                    schemas_to_add[schema_header] = inner_concept
                else:
                    inner_name = inner_concept.get("name", "")
                    field_name = f'[`{field.get("name")}`](#{inner_name.lower().replace(" ", "-")})'
                    field_type = inner_name

            if inner_concept and inner_concept.get("class_name") == "ConceptScalarType":
                field_type = inner_concept.get("name")

            # Update field type to List if applicable
            is_list = self.check_list_type(field_type_info)
            if is_list and inner_concept:
                field_type = f"list of {field_type}"

            # Update field type to Optional if applicable
            if is_optional and inner_concept:
                field_type = f"Optional[{field_type}]"

            field_type = self.refactor_names(field_type)  # type: ignore

            # Add row entry
            rows.append(
                [
                    field_name,
                    field.get("description", ""),
                    field_type,
                ]
            )

        return headers, rows

    def _is_plain_dict(self, class_name: str, field: Dict):
        return class_name == "ConceptDictionaryType" and not field.get("fields")

    def __add_book_concepts(self, usage_document, book_metadata):

        book_procedures = book_metadata.get("procedures", [])
        concepts_map = {}

        def add_concept_types_to_map(type_to_add: Dict, concepts_dict: Dict):
            class_name = type_to_add.get("class_name")
            concept_name = type_to_add.get("name")

            if concept_name and class_name in BOOK_CONCEPT_LIST and concept_name not in concepts_map:
                concepts_dict[concept_name] = type_to_add
                add_field_concepts(type_to_add, concepts_dict)

            if class_name in CONCEPTS_WITH_MULTIPLE_INNER_TYPES:
                inner_types = self.get_concept_inner_types(type_to_add)
                inner_types = sorted(inner_types, key=itemgetter("name"))

                for inner_type in inner_types:
                    inner_type_to_use = self.get_concept_type(inner_type) or inner_type
                    add_concept_types_to_map(inner_type_to_use, concepts_dict)

        def add_field_concepts(concept_dict: Dict, concepts_dict: Dict):
            if concept_dict.get("class_name") != "ConceptDictionaryType":
                return

            for variable in concept_dict.get("fields", []):
                variable_type = variable.get("t", {}).get("class_name", "")
                variable_name = variable.get("t", {}).get("name", "")

                # Check for nested concept type
                nested_concept = UsageCommand.get_concept_type(variable.get("t"))
                concept_to_add = nested_concept if nested_concept else variable.get("t")

                if nested_concept:
                    variable_type = nested_concept.get("class_name")
                    variable_name = nested_concept.get("name")

                # Add to concepts_dict if variable_name is valid and in the BOOK_CONCEPT_LIST
                if variable_name and variable_type in BOOK_CONCEPT_LIST:
                    concepts_dict[variable_name] = concept_to_add

        for procedure in book_procedures:
            concepts = (procedure.get("input_concepts") or []) + (procedure.get("output_concepts", []) or [])

            for concept in concepts:
                concept_type = self.get_concept_type(concept)
                add_concept_types_to_map(concept_type, concepts_map)

        schemas_to_add = {}

        if concepts_map:
            usage_document.add_heading("Concepts", 2)

            for name, concept_type in concepts_map.items():
                names = self.refactor_names(name, raw=True)
                usage_document.add_heading(names[0].capitalize(), 3)
                usage_document.add_horizontal_rule()

                description = concept_type.get("description", "")
                if description is None:
                    description = "No description"
                usage_document.add_paragraph(description)
                if len(names) > 1:
                    usage_document.add_paragraph(f"ALSO : {', '.join(f'`{n}`' for n in names[1:])}")

                headers, rows = self.__process_concept_fields(concept_type, schemas_to_add)

                if rows:
                    usage_document.add_table(header=headers, data=rows)

        self.__add_schemas(usage_document, schemas_to_add)

    def __add_schemas(self, usage_document: Document, schemas_to_add: Dict):
        if not schemas_to_add:
            return

        usage_document.add_horizontal_rule()

        usage_document.add_heading("Concept attribute specifications", 4)

        for name, schema_type in schemas_to_add.items():

            headers = ["Name", "Type"]
            rows = []

            usage_document.add_heading(name, 5)

            for schema_field in schema_type.get("fields", []):
                field_type_name = schema_field.get("t", "").get("name", "")
                field_type = schema_field.get("t", "")
                inner_type = self.get_concept_type(schema_field.get("t", ""))

                is_json = inner_type and inner_type.get("class_name", "") == "ConceptDictionaryType"
                if is_json:
                    field_type_name = "json"

                is_scalar = inner_type and inner_type.get("class_name", "") == "ConceptScalarType"
                if is_scalar:
                    field_type_name = inner_type.get("name", "")

                is_list = inner_type and field_type.get("class_name", "") == "ConceptListType"
                if is_list:
                    field_type_name = f"list of {field_type_name}"

                is_optional = inner_type and field_type.get("class_name", "") == "ConceptOptionalType"
                if is_optional:
                    field_type_name = f"optional[{field_type_name}]"

                field_type_name = self.refactor_names(field_type_name)

                rows.append([f'`{schema_field.get("name", "")}`', f"{field_type_name}"])

            usage_document.add_table(header=headers, data=rows)
