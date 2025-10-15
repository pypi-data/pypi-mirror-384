# -*- encoding: utf-8 -*-
"""
The analyse scripts
------------------------


"""
from __future__ import annotations
import os
import sys
import json
import click

from ..osintlib import OSIntQuest
from ..plugins import collect_plugins

from . import parser_makefile, cli, get_app, load_quest

osint_plugins = collect_plugins()
if 'directive' in osint_plugins:
    for plg in osint_plugins['directive']:
        plg.extend_quest(OSIntQuest)

__author__ = 'bibi21000 aka Sébastien GALLET'
__email__ = 'bibi21000@gmail.com'

@cli.command()
@click.argument('analysefile', default=None)
@click.pass_obj
def idents(common, analysefile):
    """List idents found in analyse and print directives"""
    sourcedir, builddir = parser_makefile(common.docdir)
    app = get_app(sourcedir=sourcedir, builddir=builddir)

    if app.config.osint_analyse_enabled is False:
        print('Plugin analyse is not enabled')
        sys.exit(1)

    if analysefile is not None:
        anals = [analysefile]
    else:
        anals = [f for f in os.listdir(os.path.join(sourcedir, app.config.osint_analyse_store))
            if os.path.isfile(os.path.join(sourcedir, app.config.osint_analyse_store, f))]
        anals += [f for f in os.listdir(os.path.join(sourcedir, app.config.osint_analyse_cache))
            if os.path.isfile(os.path.join(sourcedir, app.config.osint_analyse_cache, f)) and f not in anals]

    for anal in anals:
        analf = os.path.join(sourcedir, app.config.osint_analyse_store, os.path.splitext(os.path.basename(anal))[0] + '.json')
        if os.path.isfile(analf) is False:
            analf = os.path.join(sourcedir, app.config.osint_analyse_cache, os.path.splitext(os.path.basename(anal))[0] + '.json')

        with open(analf, 'r') as f:
            data = json.load(f)

        if 'people' in data and 'commons' in data['people']:
            for pe in data['people']['commons']:
                print(f'.. osint:ident:: {pe[0].replace(" ","")}')
                print(f'    :label: {pe[0]}')
                print('')

@cli.command()
@click.argument('analysefile', default=None)
@click.pass_obj
def links(common, analysefile):
    """List links found in analyse and print directives"""
    from ..osintlib import OSIntIdent

    sourcedir, builddir = parser_makefile(common.docdir)
    app = get_app(sourcedir=sourcedir, builddir=builddir)

    if app.config.osint_analyse_enabled is False:
        print('Plugin analyse is not enabled')
        sys.exit(1)

    if analysefile is not None:
        anals = [analysefile]
    else:
        anals = [f for f in os.listdir(os.path.join(sourcedir, app.config.osint_analyse_store))
            if os.path.isfile(os.path.join(sourcedir, app.config.osint_analyse_store, f))]
        anals += [f for f in os.listdir(os.path.join(sourcedir, app.config.osint_analyse_cache))
            if os.path.isfile(os.path.join(sourcedir, app.config.osint_analyse_cache, f)) and f not in anals]

    for anal in anals:
        analname = os.path.splitext(os.path.basename(anal))[0]
        analf = os.path.join(sourcedir, app.config.osint_analyse_store, analname + '.json')
        if os.path.isfile(analf) is False:
            analf = os.path.join(sourcedir, app.config.osint_analyse_cache, analname + '.json')

        with open(analf, 'r') as f:
            data = json.load(f)

        if 'ident' in data and 'idents' in data['ident']:
            for pe in data['ident']['idents']:
                print('.. osint:link::')
                print('    :label: link_label')
                print(f'    :from: {pe[0].replace("%s."%OSIntIdent.prefix,"")}')
                print(f'    :to: {analname}')
                print('')

@cli.command()
@click.argument('textfile', default=None)
@click.pass_obj
def analyse(common, textfile):
    """Analyse a text file and store it"""
    from ..plugins.analyselib import IdentEngine, PeopleEngine, CountriesEngine

    sourcedir, builddir = parser_makefile(common.docdir)
    app = get_app(sourcedir=sourcedir, builddir=builddir)

    if app.config.osint_analyse_enabled is False:
        print('Plugin analyse is not enabled')
        sys.exit(1)

    quest = load_quest(builddir)

    if textfile is not None:
        textfs = [textfile]
    else:
        textfs = [f for f in os.listdir(os.path.join(sourcedir, app.config.osint_text_store))
            if os.path.isfile(os.path.join(sourcedir, app.config.osint_text_store, f))]
        textfs += [f for f in os.listdir(os.path.join(sourcedir, app.config.osint_text_cache))
            if os.path.isfile(os.path.join(sourcedir, app.config.osint_text_cache, f)) and f not in textfs]

    for textf in textfs:
        textff = os.path.join(sourcedir, app.config.osint_text_store, os.path.splitext(os.path.basename(textf))[0] + '.json')
        if os.path.isfile(textff) is False:
            textff = os.path.join(sourcedir, app.config.osint_text_cache, os.path.splitext(os.path.basename(textf))[0] + '.json')

        with open(textff, 'r') as f:
            data = json.load(f)
        idents = quest.analyse_list_idents()
        orgs = quest.analyse_list_orgs()
        countries = quest.analyse_list_countries()
        print(PeopleEngine.analyse(quest, data['text'], idents=idents, orgs=orgs, countries=countries))
        print(IdentEngine.analyse(quest, data['text'], idents=idents, orgs=orgs, countries=countries))
        print(CountriesEngine.analyse(quest, data['text'], countries=countries))
        # ~ print(MoodEngine.analyse(quest, data['text'], idents=idents, orgs=orgs, countries=countries))
        # ~ print(WordsEngine.analyse(quest, data['text'], idents=idents, orgs=orgs, countries=countries, words=[], badwords=[], day_month=[]))

@cli.command()
@click.option('--missing', is_flag=True, help="Show only missing relations/links")
@click.option('--label-link', default='link_label', help="The label for links")
@click.option('--label-relation', default='relation_label', help="The label for relations")
@click.argument('ident', default=None)
@click.pass_obj
def ident(common, missing, label_link, label_relation, ident):
    """Search for ident in all analyses"""
    from ..osintlib import OSIntIdent, OSIntEvent, OSIntSource

    sourcedir, builddir = parser_makefile(common.docdir)
    app = get_app(sourcedir=sourcedir, builddir=builddir)

    if app.config.osint_analyse_enabled is False:
        print('Plugin analyse is not enabled')
        sys.exit(1)

    quest = load_quest(builddir)

    if ident.startswith(OSIntIdent.prefix) is False:
        ident = OSIntIdent.prefix + '.' + ident

    sources = []
    for source in quest.sources:
        data = quest.load_json_analyse_source(source.replace(f"{OSIntSource.prefix}.", ''), srcdir=sourcedir,
            osint_analyse_store=app.config.osint_analyse_store,
            osint_analyse_cache=app.config.osint_analyse_cache)
        if 'ident' in data and 'idents' in data['ident']:
            for idt in data['ident']['idents']:
                if idt[0] == ident:
                    sources.append(source)
    for event in quest.events:
        for source in sources:
            if source in quest.events[event].linked_sources():
                if missing is False:
                    print(event)
                else:
                    found = False
                    for link in quest.links:
                        llink = quest.links[link]
                        if llink.lfrom == ident and llink.lto == event:
                            found = True
                            break
                    if found is False:
                        print('.. osint:link::')
                        print(f'    :label: {label_link}')
                        print(f'    :from: {ident.replace("%s."%OSIntIdent.prefix,"")}')
                        print(f'    :to: {event.replace("%s."%OSIntEvent.prefix,"")}')
                        print('')
    for iident in quest.idents:
        if iident == ident:
            continue
        for source in sources:
            if source in quest.idents[iident].linked_sources():
                if missing is False:
                    print(event)
                else:
                    found = False
                    for relation in quest.relations:
                        lrelation = quest.relations[relation]
                        if (lrelation.rfrom == ident and lrelation.rto == iident) or (lrelation.rfrom == iident and lrelation.rto == ident):
                            found = True
                            break
                    if found is False:
                        print('.. osint:relation::')
                        print(f'    :label: {label_relation}')
                        print(f'    :from: {ident.replace("%s."%OSIntIdent.prefix,"")}')
                        print(f'    :to: {iident.replace("%s."%OSIntIdent.prefix,"")}')
                        print('')
