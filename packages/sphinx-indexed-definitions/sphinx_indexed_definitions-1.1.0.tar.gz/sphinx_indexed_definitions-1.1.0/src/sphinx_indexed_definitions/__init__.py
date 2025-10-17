from sphinx.application import Sphinx
from sphinx_proof.proof_type import DefinitionDirective, TheoremDirective, LemmaDirective, ConjectureDirective, CorollaryDirective, PropositionDirective, NotationDirective
import re
from docutils import nodes

SUPPORTED_NODES = ['strong','emphasis','literal']
DEFAULT_NODES = ['strong','emphasis']
CAPITAL_WORDS = list({'Cartesian','Markov','Euler','Neumann','Newton','Gauss','Lagrange','Hilbert','Frobenius','Navier','Stokes','Laplace','Cauchy','Erdős','Ramanujan',
                      'Kolmogorov','Darcy','Archimedes','Chebychev','Castigliano','Taylor','Maclaurin','Macaulay','Mohr','Jensens','Muller','Breslau','Bernoulli',
                      'Maxwell','Einstein','Froud','Reynolds','Betti','Rayleigh','Ohm','Volt','Ampère','Tesla','Curie','Turing','Murphy','Avogrado','Planck','Feynman',
                      'Nash','Bequerel','Pascal','Joule','Kelvin','Lenz','Celsius','Fahrenheit','Snell','Watt','Réaumur','Kelvin','Lenz','Celsius','Fahrenheit','Snell',
                      'Boole','Dirichlet','Euclid','Leibniz','Benford','Boyer','Dijkstra','Huygens','Lambert','Poisson','Weierstrass','Abel','Descartes','Fibonacci',
                      'Hôpital','Poincaré','Volterra','Lotka','Cramer','Schwarz','Cayley','Hamilton','Perron'})

class IndexedDefinitionDirective(DefinitionDirective):

    def run(self):        

        # first the normal parse:
        def_nodes = DefinitionDirective.run(self)
        # get the classes and do no index stuff if told so.
        classes = self.options.get('class')
        if classes is not None:
            if "skipindexing" in classes:
                return def_nodes
        # now find all indicated nodes and the (optional) title
        stuff_to_index = set()
        # find out if a title has been set (and has to be indexed)
        if self.env.config.sphinx_indexed_defs_index_titles:
            if len(self.arguments) != 0:
                title = self.arguments[0]
                if self.env.config.sphinx_indexed_defs_lowercase_indices:
                    new_string = title.lower()
                    new_math = re.findall(r"\$(.*?)\$", new_string)
                    old_math = re.findall(r"\$(.*?)\$", title)
                    for eeeee,mathe in enumerate(new_math):
                        new_string = new_string.replace(f"${mathe}$",f"${old_math[eeeee]}$")
                    for word in self.env.config.sphinx_indexed_defs_capital_words:
                        new_string = new_string.replace(f"{word.lower()}",f"{word}")
                    title = new_string.strip()
                stuff_to_index.add(title)
        for typ in self.env.config.sphinx_indexed_defs_indexed_nodes:
            assert typ in SUPPORTED_NODES, f"the node {typ} is not supported"
            list_of_nodes = def_nodes[0][1]
            for def_node in list_of_nodes:
                cls = eval("nodes."+typ)
                typ_nodes = def_node.findall(cls)
                for node in typ_nodes:
                    node_string = node.__str__()
                    node_string = node_string.replace(f"<{typ}>","").strip()
                    node_string = node_string.replace(f"</{typ}>","").strip()
                    node_string = node_string.replace(f"<{typ}/>","").strip()
                    node_string = node_string.replace("<math>","$").strip()
                    node_string = node_string.replace("</math>","$").strip()
                    if self.env.config.sphinx_indexed_defs_lowercase_indices:
                        new_string = node_string.lower().strip()
                        new_math = re.findall(r"\$(.*?)\$", new_string)
                        old_math = re.findall(r"\$(.*?)\$", node_string)
                        for eeeee,mathe in enumerate(new_math):
                            new_string = new_string.replace(f"${mathe}$",f"${old_math[eeeee]}$").strip()
                        for word in self.env.config.sphinx_indexed_defs_capital_words:
                            new_string = new_string.replace(f"{word.lower()}",f"{word}").strip()
                        node_string = new_string.strip()

                    if self.env.config.sphinx_indexed_defs_remove_brackets:
                        if "(" not in node_string:
                            # check for weird references
                            if "classes" not in node_string:
                                stuff_to_index.add(node_string)
                            elif "xref" not in node_string:
                                stuff_to_index.add(node_string)
                        else:    
                            bracketted = re.findall(r"\((.*?)\)", node_string)
                            node_string_none = node_string.strip()
                            node_string_all = node_string.strip()
                            for word in bracketted:
                                node_string_none = node_string_none.replace(f"({word})","").strip()
                                node_string_all = node_string_all.replace(f"({word})",f"{word}").strip()
                            # check for weird references
                            if "classes" not in node_string_all:
                                stuff_to_index.add(node_string_all)
                            elif "xref" not in node_string_all:
                                stuff_to_index.add(node_string_all)
                            # check for weird references
                            if "classes" not in node_string_none:
                                stuff_to_index.add(node_string_none)
                            elif "xref" not in node_string_none:
                                stuff_to_index.add(node_string_none)
                    else:
                        # check for weird references
                        if "classes" not in node_string:
                            stuff_to_index.add(node_string)
                        elif "xref" not in node_string:
                            stuff_to_index.add(node_string)

        indexes = ""
        if len(stuff_to_index)>0:
            for index in stuff_to_index:
                # check if the index should be skipped
                skip_index = False
                if index == "":
                    continue
                for regexp in self.env.config.sphinx_indexed_defs_skip_indices:
                    if re.search(regexp,index):
                        skip_index = True
                        break
                if skip_index:
                    continue
                if self.env.config.sphinx_indexed_defs_force_main:
                    indexes += f"{{index}}`!{index}`"
                else:
                    indexes += f"{{index}}`{index}`"
        start_node = [nodes.raw(None, "<div style=\"overflow:hidden;height:0px;margin:calc(var(--bs-body-font-size)*-0.5);\">", format="html")]
        end_node = [nodes.raw(None, "</div>", format="html")]
        try:
            parsed_indexes = self.parse_text_to_nodes(indexes)
        except:
            parsed_indexes = []
        node_list = start_node + parsed_indexes + end_node + def_nodes

        return node_list

def setup(app: Sphinx):

    app.add_config_value('sphinx_indexed_defs_indexed_nodes',DEFAULT_NODES,'env')
    app.add_config_value('sphinx_indexed_defs_skip_indices',[],'env')
    app.add_config_value('sphinx_indexed_defs_lowercase_indices',True,'env')
    app.add_config_value('sphinx_indexed_defs_index_titles',True,'env')
    app.add_config_value('sphinx_indexed_defs_capital_words',[],'html')
    app.add_config_value('sphinx_indexed_defs_remove_brackets',True,'env')
    app.add_config_value('sphinx_indexed_defs_force_main',True,'env')
    app.add_config_value('sphinx_indexed_defs_index_theorems',True,'env')

    app.connect('builder-inited',parse_config)

    app.setup_extension('sphinx_proof')

    app.add_directive_to_domain('prf','definition',IndexedDefinitionDirective,override=True)
    app.add_directive_to_domain('prf','theorem',IndexedTheoremDirective,override=True)
    app.add_directive_to_domain('prf','lemma',IndexedTheoremDirective,override=True)
    app.add_directive_to_domain('prf','conjecture',IndexedConjectureDirective,override=True)
    app.add_directive_to_domain('prf','corollary',IndexedCorollaryDirective,override=True)
    app.add_directive_to_domain('prf','proposition',IndexedPropositionDirective,override=True)
    app.add_directive_to_domain('prf','notation',IndexedNotationDirective,override=True)

    return {}

def parse_config(app:Sphinx):
    
    capital_words = app.config.sphinx_indexed_defs_capital_words + CAPITAL_WORDS
    app.config.sphinx_indexed_defs_capital_words = list(set(capital_words))

    pass

class IndexedTheoremDirective(TheoremDirective):

    def run(self):        

        # first the normal parse:
        def_nodes = TheoremDirective.run(self)
        # get the classes and do no index stuff if told so.
        classes = self.options.get('class')
        if classes is not None:
            if "skipindexing" in classes:
                return def_nodes
        # now find the (optional) title
        return parse_only_title(self,def_nodes)
    
class IndexedLemmaDirective(LemmaDirective):

    def run(self):        

        # first the normal parse:
        def_nodes = LemmaDirective.run(self)
        # get the classes and do no index stuff if told so.
        classes = self.options.get('class')
        if classes is not None:
            if "skipindexing" in classes:
                return def_nodes
        # now find the (optional) title
        return parse_only_title(self,def_nodes)

class IndexedConjectureDirective(ConjectureDirective):

    def run(self):        

        # first the normal parse:
        def_nodes = ConjectureDirective.run(self)
        # get the classes and do no index stuff if told so.
        classes = self.options.get('class')
        if classes is not None:
            if "skipindexing" in classes:
                return def_nodes
        # now find the (optional) title
        return parse_only_title(self,def_nodes)
    
class IndexedCorollaryDirective(CorollaryDirective):

    def run(self):        

        # first the normal parse:
        def_nodes = CorollaryDirective.run(self)
        # get the classes and do no index stuff if told so.
        classes = self.options.get('class')
        if classes is not None:
            if "skipindexing" in classes:
                return def_nodes
        # now find the (optional) title
        return parse_only_title(self,def_nodes)
    
class IndexedPropositionDirective(PropositionDirective):

    def run(self):        

        # first the normal parse:
        def_nodes = PropositionDirective.run(self)
        # get the classes and do no index stuff if told so.
        classes = self.options.get('class')
        if classes is not None:
            if "skipindexing" in classes:
                return def_nodes
        # now find the (optional) title
        return parse_only_title(self,def_nodes)
    
class IndexedNotationDirective(NotationDirective):

    def run(self):        

        # first the normal parse:
        def_nodes = NotationDirective.run(self)
        # get the classes and do no index stuff if told so.
        classes = self.options.get('class')
        if classes is not None:
            if "skipindexing" in classes:
                return def_nodes
        # now find the (optional) title
        return parse_only_title(self,def_nodes)
       
def parse_only_title(self,def_nodes):
        
    stuff_to_index = set()
    # find out if a title has been set (and has to be indexed)
    if self.env.config.sphinx_indexed_defs_index_theorems:
        if len(self.arguments) != 0:
            title = self.arguments[0]
            if self.env.config.sphinx_indexed_defs_lowercase_indices:
                new_string = title.lower()
                new_math = re.findall(r"\$(.*?)\$", new_string)
                old_math = re.findall(r"\$(.*?)\$", title)
                for eeeee,mathe in enumerate(new_math):
                    new_string = new_string.replace(f"${mathe}$",f"${old_math[eeeee]}$")
                for word in self.env.config.sphinx_indexed_defs_capital_words:
                    new_string = new_string.replace(f"{word.lower()}",f"{word}")
                title = new_string.strip()
            stuff_to_index.add(title)

    indexes = ""
    if len(stuff_to_index)>0:
        for index in stuff_to_index:
            # check if the index should be skipped
            skip_index = False
            if index == "":
                continue
            for regexp in self.env.config.sphinx_indexed_defs_skip_indices:
                if re.search(regexp,index):
                    skip_index = True
                    break
            if skip_index:
                continue
            indexes += f"{{index}}`{index}`"
    start_node = [nodes.raw(None, "<div style=\"overflow:hidden;height:0px;margin:calc(var(--bs-body-font-size)*-0.5);\">", format="html")]
    end_node = [nodes.raw(None, "</div>", format="html")]
    try:
        parsed_indexes = self.parse_text_to_nodes(indexes)
    except:
        parsed_indexes = []
    node_list = start_node + parsed_indexes + end_node + def_nodes

    return node_list
