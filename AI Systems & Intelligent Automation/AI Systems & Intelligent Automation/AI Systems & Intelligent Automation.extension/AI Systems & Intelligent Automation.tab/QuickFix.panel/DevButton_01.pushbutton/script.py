# -*- coding: utf-8 -*-
__title__ = "AI"
__doc__ = """AI"""

import clr
import os
import sys
import json
import subprocess
import requests
import re
import time
import System

from System import Action

from pyrevit import revit, DB, forms, script
from pyrevit import script as pyscript
import System.Windows.Forms as WinForms

uidoc = revit.uidoc
doc = revit.doc

# === Config ===
OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3:mini"
XAML_PATH = "UI.xaml"

# print("RUNNING AI script from:", __file__)

logger = pyscript.get_logger()

def _silent_alert(msg, title="pyRevit", exitscript=False, **kwargs):
    # No icon => no Windows system sound
    WinForms.MessageBox.Show(
        str(msg), str(title),
        WinForms.MessageBoxButtons.OK,
        WinForms.MessageBoxIcon.None
    )
    if exitscript:
        pyscript.exit()

# Replace pyRevit's alert with our silent version
forms.alert = _silent_alert
# --- end silent override---
# === Helper Functions ===


def do_nothing():
    pass


def safe_str(x):
    try:
        if x is None:
            return "(none)"
        return str(x)
    except:
        return "(err)"


def ollama_is_installed():
    try:
        result = subprocess.Popen(
            ["ollama", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = result.communicate()
        return result.returncode == 0
    except Exception:
        return False


def ollama_model_installed(model_name):
    try:
        result = subprocess.Popen(
            ["ollama", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = result.communicate()
        models = []
        if result.returncode == 0:
            lines = out.decode("utf-8").splitlines()
            for line in lines[1:]:
                parts = line.strip().split()
                if parts:
                    models.append(parts[0])
            for m in models:
                if m == model_name:
                    return True
        return False
    except Exception:
        return False


def pull_ollama_model(model_name):
    try:
        forms.alert(
            "Pulling model: {} ... This may take a few minutes on first install.".format(
                model_name
            ),
            title="Ollama Copilot",
        )
        result = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = result.communicate()
        if result.returncode == 0:
            forms.alert(
                "Model {} installed successfully!".format(model_name),
                title="Ollama Copilot",
            )
            return True
        else:
            forms.alert("Error pulling model: {}".format(err), title="Ollama Copilot")
            return False
    except Exception as e:
        forms.alert("Error pulling model: {}".format(str(e)), title="Ollama Copilot")
        return False


def send_ollama_chat(model_name, prompt):
    data = {"model": model_name, "prompt": prompt}
    try:
        resp = requests.post(OLLAMA_API_URL, json=data, stream=True, timeout=60)
        full_reply = ""
        # resp.iter_lines() yields each JSON object as a line
        for line in resp.iter_lines():
            if line:
                try:
                    msg = json.loads(line)
                    if "response" in msg:
                        full_reply += msg["response"]
                    if "done" in msg and msg["done"]:
                        break
                except Exception as e:
                    # Skip lines that aren't valid JSON
                    continue
        return full_reply.strip()
    except Exception as e:
        return "Error: Could not connect to Ollama ({})".format(str(e))


def get_all_models():
    try:
        result = subprocess.Popen(
            ["ollama", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = result.communicate()
        models = []
        if result.returncode == 0:
            lines = out.decode("utf-8").splitlines()
            # Skip header row
            for line in lines[1:]:
                parts = line.strip().split()
                if parts:
                    models.append(parts[0])
        return models
    except Exception as e:
        print("get_all_models error:", str(e))
        return []


def extract_python_code(text):
    """Extract python code blocks from markdown-formatted LLM output."""
    code_blocks = re.findall(r"```python\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if not code_blocks:
        # Try to catch blocks where 'python' is on its own line
        code_blocks = re.findall(
            r"```[\s\n]*python[\s\n]*(.*?)```", text, re.DOTALL | re.IGNORECASE
        )
    return [code.strip() for code in code_blocks]


def safe_str_list(lst):
    return [str(x) if x is not None else "(none)" for x in lst]


# --- STRUCTURAL ---
def select_all_columns(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    columns = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralColumns)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [col.Id for col in columns]
    rows = []
    total_volume = 0
    for col in columns:
        name = get_elem_name(col)
        t = col.Document.GetElement(col.GetTypeId())
        typ = t.Name if (t is not None and hasattr(t, "Name")) else "(no type)"
        mark = safe_str(
            col.LookupParameter("Mark").AsString()
            if col.LookupParameter("Mark")
            else "(none)"
        )
        vol_param = col.LookupParameter("Volume")
        v = 0
        if vol_param:
            try:
                v = vol_param.AsDouble() * 0.0283168  # ft3 to m3
            except:
                pass
        total_volume += v
        # Get materials
        mat_list = []
        for mid in col.GetMaterialIds(False):
            mat = doc.GetElement(mid)
            mname = safe_str(mat.Name if mat else str(mid.IntegerValue))
            try:
                mvol = col.GetMaterialVolume(mid) * 0.0283168
            except:
                mvol = 0
            mat_list.append("{}: {:.3f} m³".format(mname, float(mvol)))
        mat_str = ", ".join(mat_list) if mat_list else "(none)"
        rows.append(
            "Name: {}, Type: {}, Mark: {}, Volume: {:.3f} m³, Materials: {}".format(
                name, typ, mark, float(v), mat_str
            )
        )
    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} columns.\n".format(len(columns))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(rows))
    msg += "\nTotal Volume: {:.3f} m³".format(float(total_volume))
    return msg


def select_all_beams(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    beams = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralFraming)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [b.Id for b in beams]
    rows = []
    total_length = 0.0
    for b in beams:
        name = get_elem_name(b)
        t = b.Document.GetElement(b.GetTypeId())
        typ = t.Name if (t is not None and hasattr(t, "Name")) else "(no type)"
        length_param = b.LookupParameter("Length")
        length = 0.0
        if length_param:
            try:
                length = float(length_param.AsDouble() * 0.3048)  # ft to m
            except:
                length = 0.0
        total_length += length
        # Material breakdown
        mat_list = []
        for mid in b.GetMaterialIds(False):
            mat = doc.GetElement(mid)
            mname = (
                mat.Name if (mat and hasattr(mat, "Name")) else str(mid.IntegerValue)
            )
            try:
                mvol = float(b.GetMaterialVolume(mid) * 0.0283168)
            except:
                mvol = 0.0
            try:
                marea = float(b.GetMaterialArea(mid) * 0.092903)
            except:
                marea = 0.0
            mat_list.append("{}: {:.2f} m³, {:.2f} m²".format(mname, mvol, marea))
        mat_str = ", ".join(mat_list) if mat_list else "(none)"
        rows.append(
            "Name: {}, Type: {}, Length: {:.2f} m, Materials: {}".format(
                name, typ, length, mat_str
            )
        )
    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} beams.\n".format(len(beams))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(rows))
    msg += "\nTotal Length: {:.2f} m".format(total_length)
    return msg


def select_all_foundations(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    foundations = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralFoundation)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [f.Id for f in foundations]
    rows = []
    total_volume = 0.0
    for f in foundations:
        # Safer name access
        if hasattr(f, "Name"):
            name = safe_str(f.Name)
        else:
            name = "(no name)"
        t = f.Document.GetElement(f.GetTypeId())
        typ = t.Name if t and hasattr(t, "Name") else "(no type)"
        vol_param = f.LookupParameter("Volume")
        vol = 0.0
        if vol_param:
            try:
                vol = float(vol_param.AsDouble() * 0.0283168)
            except:
                vol = 0.0
        total_volume += vol
        mat_list = []
        for mid in f.GetMaterialIds(False):
            mat = doc.GetElement(mid)
            # Always check for .Name attribute
            mname = mat.Name if mat and hasattr(mat, "Name") else str(mid.IntegerValue)
            try:
                mvol = float(f.GetMaterialVolume(mid) * 0.0283168)
            except:
                mvol = 0.0
            try:
                marea = float(f.GetMaterialArea(mid) * 0.092903)
            except:
                marea = 0.0
            mat_list.append("{}: {:.2f} m³, {:.2f} m²".format(mname, mvol, marea))
        mat_str = ", ".join(mat_list) if mat_list else "(none)"
        rows.append(
            "Name: {}, Type: {}, Volume: {:.2f} m³, Materials: {}".format(
                name, typ, vol, mat_str
            )
        )
    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} foundations.\n".format(len(foundations))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(rows))
    msg += "\nTotal Volume: {:.2f} m³".format(total_volume)
    return msg


def select_all_rebars(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    rebars = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Rebar)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [r.Id for r in rebars]
    rows = []
    total_length = 0.0
    total_count = 0
    total_volume = 0.0
    for r in rebars:
        # Get type/name
        try:
            t = r.Document.GetElement(r.GetTypeId())
            name = get_elem_name(r)
        except:
            name = "(no name)"

        # Length per bar
        try:
            bar_length = r.LookupParameter("Bar Length").AsDouble() * 0.3048
        except:
            bar_length = 0

        # Quantity
        try:
            count = r.LookupParameter("Quantity").AsInteger()
        except:
            count = 1

        # Volume per bar (if exists)
        try:
            bar_vol = r.LookupParameter("Bar Volume").AsDouble() * 0.0283168
        except:
            bar_vol = 0

        # Diameters
        try:
            diameter = r.LookupParameter("Bar Diameter").AsDouble() * 0.3048
        except:
            diameter = None

        # Material
        try:
            mats = r.GetMaterialIds(False)
            mat_name = None
            for mid in mats:
                mat = doc.GetElement(mid)
                if mat:
                    mat_name = get_elem_name(mat)
                    break
            if not mat_name:
                mat_name = "(none)"
        except:
            mat_name = "(none)"

        length_total = bar_length * count
        if bar_vol is not None:
            volume_total = bar_vol * count
        else:
            # Estimate volume if bar_vol not available (as solid cylinder)
            if diameter is not None and bar_length > 0:
                radius = float(diameter) / 2.0
                volume_total = 3.14159265 * (radius**2) * bar_length * count
            else:
                volume_total = 0.0

        total_length += length_total
        total_count += count
        total_volume += volume_total

        # Format values safely
        if diameter is not None and isinstance(diameter, (float, int)):
            diameter_str = "{:.3f}".format(float(diameter))
        else:
            diameter_str = "(none)"
        if bar_vol is not None and isinstance(bar_vol, (float, int)):
            bar_vol_str = "{:.4f}".format(float(bar_vol))
        else:
            bar_vol_str = "(est)" if volume_total > 0 else "(none)"
        if volume_total is not None and isinstance(volume_total, (float, int)):
            volume_total_str = "{:.4f}".format(float(volume_total))
        else:
            volume_total_str = "(none)"

        rows.append(
            "Name/Type: {}, Quantity: {}, Length per bar: {:.2f} m, Total Length: {:.2f} m, Diameter: {} m, Material: {}, Bar Volume: {}, Total Volume: {}".format(
                name,
                count,
                bar_length,
                length_total,
                diameter_str,
                mat_name,
                bar_vol_str,
                volume_total_str,
            )
        )

    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} rebars.\n".format(len(rebars))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(rows))
    msg += "\nTotal rebars: {}\nTotal rebar length: {:.2f} m\nTotal rebar volume: {:.4f} m³".format(
        total_count, total_length, total_volume
    )
    return msg


def select_all_floors(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    floors = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Floors)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [f.Id for f in floors]
    rows = []
    total_area = 0.0
    total_vol = 0.0

    for f in floors:
        name = get_elem_name(f)
        t = f.Document.GetElement(f.GetTypeId())
        typ = t.Name if (t and hasattr(t, "Name")) else "(no type)"

        area = 0.0
        vol = 0.0
        ap = f.LookupParameter("Area")
        vp = f.LookupParameter("Volume")
        if ap:
            try:
                area = ap.AsDouble() * 0.092903
            except:
                pass
        if vp:
            try:
                vol = vp.AsDouble() * 0.0283168
            except:
                pass
        total_area += area
        total_vol += vol

        mat_list = []
        for mid in f.GetMaterialIds(False):
            mat = doc.GetElement(mid)
            mname = (
                mat.Name if (mat and hasattr(mat, "Name")) else str(mid.IntegerValue)
            )
            try:
                mvol = f.GetMaterialVolume(mid) * 0.0283168
            except:
                mvol = 0.0
            try:
                marea = f.GetMaterialArea(mid) * 0.092903
            except:
                marea = 0.0
            mat_list.append(
                "{}: {:.2f} m³, {:.2f} m²".format(mname, float(mvol), float(marea))
            )
        mat_str = ", ".join(mat_list) if mat_list else "(none)"

        rows.append(
            "Name: {}, Type: {}, Area: {:.2f} m², Volume: {:.2f} m³, Materials: {}".format(
                name, typ, float(area), float(vol), mat_str
            )
        )

    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} floors.\n".format(len(floors))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(floors))
    msg += "\nTotal Area: {:.2f} m²\nTotal Volume: {:.2f} m³".format(
        float(total_area), float(total_vol)
    )
    return msg


def select_all_ceilings(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    ceilings = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Ceilings)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [c.Id for c in ceilings]
    rows = []
    total_area = 0.0
    total_vol = 0.0

    for c in ceilings:
        name = get_elem_name(c)
        t = c.Document.GetElement(c.GetTypeId())
        typ = t.Name if (t and hasattr(t, "Name")) else "(no type)"

        area = 0.0
        vol = 0.0
        ap = c.LookupParameter("Area")
        vp = c.LookupParameter("Volume")
        if ap:
            try:
                area = ap.AsDouble() * 0.092903
            except:
                pass
        if vp:
            try:
                vol = vp.AsDouble() * 0.0283168
            except:
                pass
        total_area += area
        total_vol += vol

        mat_list = []
        for mid in c.GetMaterialIds(False):
            mat = doc.GetElement(mid)
            mname = (
                mat.Name if (mat and hasattr(mat, "Name")) else str(mid.IntegerValue)
            )
            try:
                mvol = c.GetMaterialVolume(mid) * 0.0283168
            except:
                mvol = 0.0
            try:
                marea = c.GetMaterialArea(mid) * 0.092903
            except:
                marea = 0.0
            mat_list.append(
                "{}: {:.2f} m³, {:.2f} m²".format(mname, float(mvol), float(marea))
            )
        mat_str = ", ".join(mat_list) if mat_list else "(none)"

        rows.append(
            "Name: {}, Type: {}, Area: {:.2f} m², Volume: {:.2f} m³, Materials: {}".format(
                name, typ, float(area), float(vol), mat_str
            )
        )

    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} ceilings.\n".format(len(ceilings))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(ceilings))
    msg += "\nTotal Area: {:.2f} m²\nTotal Volume: {:.2f} m³".format(
        float(total_area), float(total_vol)
    )
    return msg


def select_all_roofs(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    roofs = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Roofs)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [r.Id for r in roofs]
    rows = []
    total_area = 0.0
    total_vol = 0.0

    for r in roofs:
        name = get_elem_name(r)
        t = r.Document.GetElement(r.GetTypeId())
        typ = t.Name if (t and hasattr(t, "Name")) else "(no type)"

        area = 0.0
        vol = 0.0
        ap = r.LookupParameter("Area")
        vp = r.LookupParameter("Volume")
        if ap:
            try:
                area = ap.AsDouble() * 0.092903
            except:
                pass
        if vp:
            try:
                vol = vp.AsDouble() * 0.0283168
            except:
                pass
        total_area += area
        total_vol += vol

        mat_list = []
        for mid in r.GetMaterialIds(False):
            mat = doc.GetElement(mid)
            mname = (
                mat.Name if (mat and hasattr(mat, "Name")) else str(mid.IntegerValue)
            )
            try:
                mvol = r.GetMaterialVolume(mid) * 0.0283168
            except:
                mvol = 0.0
            try:
                marea = r.GetMaterialArea(mid) * 0.092903
            except:
                marea = 0.0
            mat_list.append(
                "{}: {:.2f} m³, {:.2f} m²".format(mname, float(mvol), float(marea))
            )
        mat_str = ", ".join(mat_list) if mat_list else "(none)"

        rows.append(
            "Name: {}, Type: {}, Area: {:.2f} m², Volume: {:.2f} m³, Materials: {}".format(
                name, typ, float(area), float(vol), mat_str
            )
        )

    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} roofs.\n".format(len(roofs))
    msg += "\n".join(rows[:20])
    if len(roofs) > 20:
        msg += "\n... (showing first 20 of {})".format(len(roofs))
    msg += "\nTotal Area: {:.2f} m²\nTotal Volume: {:.2f} m³".format(
        float(total_area), float(total_vol)
    )
    return msg


def count_floors(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    floors = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Floors)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    return "Total floors: {}".format(len(floors))


def count_ceilings(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    ceilings = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Ceilings)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    return "Total ceilings: {}".format(len(ceilings))


def count_roofs(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    roofs = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Roofs)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    return "Total roofs: {}".format(len(roofs))


def count_rebars(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    rebars = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Rebar)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    return "There are {} rebars in the model.".format(len(rebars))


def count_columns(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    cols = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralColumns)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    return "Total structural columns: {}".format(len(cols))


def delete_all_columns(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector, Transaction

    cols = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralColumns)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [c.Id for c in cols]
    t = Transaction(doc, "Delete all columns")
    t.Start()
    for i in ids:
        doc.Delete(i)
    t.Commit()
    return "Deleted {} columns.".format(len(ids))


def total_structural_volume(doc, uidoc):
    from Autodesk.Revit.DB import (
        BuiltInCategory,
        FilteredElementCollector,
        ParameterType,
    )

    elements = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralFraming)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    total_vol = 0
    for elem in elements:
        param = elem.LookupParameter("Volume")
        if param:
            try:
                total_vol += param.AsDouble()
            except:
                pass
    m3 = total_vol * 0.0283168  # Revit internal units to m3
    return "Total volume of structural framing: {:.2f} m³".format(m3)


# --- ARCHITECTURAL ---
def select_all_walls(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    walls = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Walls)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [w.Id for w in walls]
    rows = []
    total_area = 0
    total_vol = 0
    for w in walls:
        name = get_elem_name(w)
        t = w.Document.GetElement(w.GetTypeId())
        typ = t.Name if (t is not None and hasattr(t, "Name")) else "(no type)"
        mark = (
            w.LookupParameter("Mark").AsString()
            if w.LookupParameter("Mark")
            else "(none)"
        )
        area_param = w.LookupParameter("Area")
        area = 0
        if area_param:
            try:
                area = area_param.AsDouble() * 0.092903
            except:
                pass
        vol_param = w.LookupParameter("Volume")
        vol = 0
        if vol_param:
            try:
                vol = vol_param.AsDouble() * 0.0283168
            except:
                pass
        total_area += area
        total_vol += vol
        # Material breakdown
        mat_list = []
        for mid in w.GetMaterialIds(False):
            mat = doc.GetElement(mid)
            mname = (
                mat.Name if (mat and hasattr(mat, "Name")) else str(mid.IntegerValue)
            )
            try:
                mvol = w.GetMaterialVolume(mid) * 0.0283168
                marea = w.GetMaterialArea(mid) * 0.092903
            except:
                mvol = marea = 0
            mat_list.append(
                "{}: {:.2f} m³, {:.2f} m²".format(mname, float(mvol), float(marea))
            )
        mat_str = ", ".join(mat_list) if mat_list else "(none)"
        rows.append(
            "Name: {}, Type: {}, Mark: {}, Area: {:.2f} m², Volume: {:.2f} m³, Materials: {}".format(
                name, typ, mark, float(area), float(vol), mat_str
            )
        )
    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} walls.\n".format(len(walls))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(rows))
    msg += "\nTotal Area: {:.2f} m²\nTotal Volume: {:.2f} m³".format(
        float(total_area), float(total_vol)
    )
    return msg


def select_all_windows(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    windows = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Windows)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [w.Id for w in windows]
    rows = []
    for w in windows:
        name = get_elem_name(w)  # for window/door/wall 'w'
        t = w.Document.GetElement(w.GetTypeId())
        typ = t.Name if (t is not None and hasattr(t, "Name")) else "(no type)"
        mark = safe_str(
            w.LookupParameter("Mark").AsString()
            if w.LookupParameter("Mark")
            else "(none)"
        )
        area = None
        vol = None
        area_param = w.LookupParameter("Area")
        vol_param = w.LookupParameter("Volume")
        if area_param:
            try:
                area = area_param.AsDouble() * 0.092903
            except:
                area = None
        if vol_param:
            try:
                vol = vol_param.AsDouble() * 0.0283168
            except:
                vol = None
        rows.append(
            "Name: {}, Type: {}, Mark: {}, Area: {} m², Volume: {} m³".format(
                name,
                typ,
                mark,
                "{:.2f}".format(area) if area else "(none)",
                "{:.2f}".format(vol) if vol else "(none)",
            )
        )
    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} windows.\n".format(len(windows))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(rows))
    return msg


def select_all_doors(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    doors = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Doors)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [d.Id for d in doors]
    rows = []
    for d in doors:
        name = get_elem_name(d)
        t = d.Document.GetElement(d.GetTypeId())
        typ = t.Name if (t is not None and hasattr(t, "Name")) else "(no type)"
        mark = safe_str(
            d.LookupParameter("Mark").AsString()
            if d.LookupParameter("Mark")
            else "(none)"
        )
        area = None
        vol = None
        area_param = d.LookupParameter("Area")
        vol_param = d.LookupParameter("Volume")
        if area_param:
            try:
                area = area_param.AsDouble() * 0.092903
            except:
                area = None
        if vol_param:
            try:
                vol = vol_param.AsDouble() * 0.0283168
            except:
                vol = None
        rows.append(
            "Name: {}, Type: {}, Mark: {}, Area: {} m², Volume: {} m³".format(
                name,
                typ,
                mark,
                "{:.2f}".format(area) if area else "(none)",
                "{:.2f}".format(vol) if vol else "(none)",
            )
        )
    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} doors.\n".format(len(doors))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(rows))
    return msg


def total_room_area(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    rooms = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Rooms)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    total_area = 0
    names = []
    levels = []
    for room in rooms:
        area = 0
        name = (
            room.LookupParameter("Name").AsString()
            if room.LookupParameter("Name")
            else "(no name)"
        )
        names.append(name)
        area_param = room.LookupParameter("Area")
        if area_param:
            try:
                area = area_param.AsDouble() * 0.092903  # ft2 to m2
            except:
                pass
        total_area += area
        level_param = room.LookupParameter("Level")
        if level_param:
            levels.append(level_param.AsValueString())
    msg = "Room count: {}\n".format(len(rooms))
    msg += "Room names: {}\n".format(
        ", ".join(names[:10]) + (" ..." if len(names) > 10 else "")
    )
    msg += "Levels: {}\n".format(
        ", ".join(set([l for l in levels if l])) if levels else "(none)"
    )
    msg += "Total room area: {:.2f} m²\n".format(total_area)
    return msg


def tag_all_rooms(doc, uidoc):
    from Autodesk.Revit.DB import (
        BuiltInCategory,
        FilteredElementCollector,
        Transaction,
        XYZ,
    )

    rooms = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Rooms)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    count = 0
    t = Transaction(doc, "Tag all rooms")
    t.Start()
    for room in rooms:
        loc = room.Location
        pt = None
        if hasattr(loc, "Point"):
            pt = loc.Point
        elif hasattr(loc, "Curve"):
            pt = loc.Curve.Evaluate(0.5, True)
        if pt:
            doc.Create.NewRoomTag(room, pt, None)
            count += 1
    t.Commit()
    return "Tagged {} rooms.".format(count)


def delete_all_doors(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector, Transaction

    doors = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Doors)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [d.Id for d in doors]
    count = 0
    t = Transaction(doc, "Delete all doors")
    t.Start()
    for i in ids:
        doc.Delete(i)
        count += 1
    t.Commit()
    return "Deleted {} doors.".format(count)


def delete_all_walls(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector, Transaction

    walls = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Walls)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [w.Id for w in walls]
    t = Transaction(doc, "Delete all walls")
    t.Start()
    for i in ids:
        doc.Delete(i)
    t.Commit()
    return "Deleted {} walls.".format(len(ids))


def delete_all_ceilings(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector, Transaction

    ceilings = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Ceilings)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [c.Id for c in ceilings]
    t = Transaction(doc, "Delete all ceilings")
    t.Start()
    for i in ids:
        doc.Delete(i)
    t.Commit()
    return "Deleted {} ceilings.".format(len(ids))


def delete_all_roofs(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector, Transaction

    roofs = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Roofs)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [r.Id for r in roofs]
    t = Transaction(doc, "Delete all roofs")
    t.Start()
    for i in ids:
        doc.Delete(i)
    t.Commit()
    return "Deleted {} roofs.".format(len(ids))


def total_ceiling_area_volume(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    ceilings = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Ceilings)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    total_area_ft2 = 0.0
    total_vol_ft3 = 0.0
    for c in ceilings:
        ap = c.LookupParameter("Area")
        vp = c.LookupParameter("Volume")
        if ap:
            try:
                total_area_ft2 += ap.AsDouble()
            except:
                pass
        if vp:
            try:
                total_vol_ft3 += vp.AsDouble()
            except:
                pass
    total_area_m2 = total_area_ft2 * 0.092903
    total_vol_m3 = total_vol_ft3 * 0.0283168
    return (
        "Ceilings — Count: {} | Total Area: {:.2f} m² | Total Volume: {:.2f} m³".format(
            len(ceilings), total_area_m2, total_vol_m3
        )
    )


def total_roof_area_volume(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    roofs = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Roofs)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    total_area_ft2 = 0.0
    total_vol_ft3 = 0.0
    for r in roofs:
        ap = r.LookupParameter("Area")
        vp = r.LookupParameter("Volume")
        if ap:
            try:
                total_area_ft2 += ap.AsDouble()
            except:
                pass
        if vp:
            try:
                total_vol_ft3 += vp.AsDouble()
            except:
                pass
    total_area_m2 = total_area_ft2 * 0.092903
    total_vol_m3 = total_vol_ft3 * 0.0283168
    return "Roofs — Count: {} | Total Area: {:.2f} m² | Total Volume: {:.2f} m³".format(
        len(roofs), total_area_m2, total_vol_m3
    )


def count_walls(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    walls = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Walls)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    return "Total walls: {}".format(len(walls))


def material_takeoff_walls(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    walls = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Walls)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    mat_vol = {}
    mat_area = {}
    for w in walls:
        mats = w.GetMaterialIds(False)
        for mid in mats:
            mat = doc.GetElement(mid)
            mname = (
                str(mat.Name)
                if mat and hasattr(mat, "Name") and mat.Name
                else str(mid.IntegerValue)
            )
            # Try to get material volume and area
            try:
                vol = w.GetMaterialVolume(mid)
                area = w.GetMaterialArea(mid)
            except:
                vol = 0
                area = 0
            if mname not in mat_vol:
                mat_vol[mname] = 0
                mat_area[mname] = 0
            mat_vol[mname] += vol * 0.0283168  # ft3 to m3
            mat_area[mname] += area * 0.092903  # ft2 to m2
    msg = "Wall Material Takeoff:\n"
    for mname in mat_vol:
        msg += "    {}: {:.2f} m³, {:.2f} m²\n".format(
            mname, mat_vol[mname], mat_area[mname]
        )
    return msg


def material_takeoff_floors(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    floors = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Floors)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    mat_vol = {}
    mat_area = {}
    for f in floors:
        mats = f.GetMaterialIds(False)
        for mid in mats:
            mat = doc.GetElement(mid)
            mname = mat.Name if mat else str(mid.IntegerValue)
            try:
                vol = f.GetMaterialVolume(mid)
                area = f.GetMaterialArea(mid)
            except:
                vol = 0
                area = 0
            if mname not in mat_vol:
                mat_vol[mname] = 0
                mat_area[mname] = 0
            mat_vol[mname] += vol * 0.0283168
            mat_area[mname] += area * 0.092903
    msg = "Floor Material Takeoff:\n"
    for mname in mat_vol:
        msg += "    {}: {:.2f} m³, {:.2f} m²\n".format(
            mname, mat_vol[mname], mat_area[mname]
        )
    return msg


def material_takeoff_columns(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    columns = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralColumns)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    vols = []
    for c in columns:
        vol_param = c.LookupParameter("Volume")
        v = 0
        if vol_param:
            try:
                v = vol_param.AsDouble() * 0.0283168  # ft³ to m³
            except:
                pass
        vols.append(v)
    msg = "Structural Column Total Volume: {:.3f} m³\n".format(sum(vols))
    return msg


def material_takeoff_beams(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    beams = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralFraming)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    mat_vol = {}
    mat_area = {}
    for b in beams:
        mats = b.GetMaterialIds(False)
        for mid in mats:
            mat = doc.GetElement(mid)
            mname = mat.Name if mat else str(mid.IntegerValue)
            try:
                vol = b.GetMaterialVolume(mid)
                area = b.GetMaterialArea(mid)
            except:
                vol = 0
                area = 0
            if mname not in mat_vol:
                mat_vol[mname] = 0
                mat_area[mname] = 0
            mat_vol[mname] += vol * 0.0283168
            mat_area[mname] += area * 0.092903
    msg = "Beam (Structural Framing) Material Takeoff:\n"
    for mname in mat_vol:
        msg += "    {}: {:.2f} m³, {:.2f} m²\n".format(
            mname, mat_vol[mname], mat_area[mname]
        )
    return msg


def material_takeoff_roofs(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    roofs = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Roofs)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    mat_vol = {}
    mat_area = {}
    for r in roofs:
        mats = r.GetMaterialIds(False)
        for mid in mats:
            mat = doc.GetElement(mid)
            mname = mat.Name if mat else str(mid.IntegerValue)
            try:
                vol = r.GetMaterialVolume(mid)
                area = r.GetMaterialArea(mid)
            except:
                vol = 0
                area = 0
            if mname not in mat_vol:
                mat_vol[mname] = 0
                mat_area[mname] = 0
            mat_vol[mname] += vol * 0.0283168
            mat_area[mname] += area * 0.092903
    msg = "Roof Material Takeoff:\n"
    for mname in mat_vol:
        msg += "    {}: {:.2f} m³, {:.2f} m²\n".format(
            mname, mat_vol[mname], mat_area[mname]
        )
    return msg


def material_takeoff_stairs(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    stairs = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Stairs)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    mat_vol = {}
    mat_area = {}
    for s in stairs:
        mats = s.GetMaterialIds(False)
        for mid in mats:
            mat = doc.GetElement(mid)
            mname = mat.Name if mat else str(mid.IntegerValue)
            try:
                vol = s.GetMaterialVolume(mid)
                area = s.GetMaterialArea(mid)
            except:
                vol = 0
                area = 0
            if mname not in mat_vol:
                mat_vol[mname] = 0
                mat_area[mname] = 0
            mat_vol[mname] += vol * 0.0283168
            mat_area[mname] += area * 0.092903
    msg = "Stair Material Takeoff:\n"
    for mname in mat_vol:
        msg += "    {}: {:.2f} m³, {:.2f} m²\n".format(
            mname, mat_vol[mname], mat_area[mname]
        )
    return msg


def material_takeoff_curtainpanels(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    panels = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_CurtainWallPanels)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    mat_vol = {}
    mat_area = {}
    for p in panels:
        mats = p.GetMaterialIds(False)
        for mid in mats:
            mat = doc.GetElement(mid)
            mname = mat.Name if mat else str(mid.IntegerValue)
            try:
                vol = p.GetMaterialVolume(mid)
                area = p.GetMaterialArea(mid)
            except:
                vol = 0
                area = 0
            if mname not in mat_vol:
                mat_vol[mname] = 0
                mat_area[mname] = 0
            mat_vol[mname] += vol * 0.0283168
            mat_area[mname] += area * 0.092903
    msg = "Curtain Panel Material Takeoff:\n"
    for mname in mat_vol:
        msg += "    {}: {:.2f} m³, {:.2f} m²\n".format(
            mname, mat_vol[mname], mat_area[mname]
        )
    return msg


def material_takeoff_rebar(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    rebars = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Rebar)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    mat_len = {}
    mat_count = {}
    for r in rebars:
        mats = r.GetMaterialIds(False)
        for mid in mats:
            mat = doc.GetElement(mid)
            mname = mat.Name if mat else str(mid.IntegerValue)
            try:
                length = (
                    r.LookupParameter("Bar Length").AsDouble() * 0.3048
                )  # feet to meters
                count = r.LookupParameter("Quantity").AsInteger()
            except:
                length = 0
                count = 0
            if mname not in mat_len:
                mat_len[mname] = 0
                mat_count[mname] = 0
            mat_len[mname] += length * count
            mat_count[mname] += count
    msg = "Rebar Material Takeoff:\n"
    for mname in mat_len:
        msg += "    {}: {:.2f} m total, {} bars\n".format(
            mname, mat_len[mname], mat_count[mname]
        )
    return msg


# --- MECHANICAL ---
def select_all_ducts(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    ducts = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_DuctCurves)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [d.Id for d in ducts]
    rows = []
    total_length = 0.0
    for d in ducts:
        t = d.Document.GetElement(d.GetTypeId())
        typ = t.Name if t and hasattr(t, "Name") else "(no type)"
        system_param = d.LookupParameter("System Name")
        system = system_param.AsString() if system_param else "(no system)"
        length_param = d.LookupParameter("Length")
        length = 0.0
        if length_param:
            try:
                length = float(length_param.AsDouble() * 0.3048)
            except:
                length = 0.0
        total_length += length
        rows.append(
            "Type: {}, System: {}, Length: {:.2f} m".format(typ, system, length)
        )
    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} ducts.\n".format(len(ducts))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(rows))
    msg += "\nTotal Length: {:.2f} m".format(total_length)
    return msg


def select_all_pipes(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    pipes = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_PipeCurves)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [p.Id for p in pipes]
    rows = []
    total_length = 0.0
    for p in pipes:
        name = p.Name if hasattr(p, "Name") else "(no name)"
        t = p.Document.GetElement(p.GetTypeId())
        typ = t.Name if t and hasattr(t, "Name") else "(no type)"
        system_param = p.LookupParameter("System Name")
        system = system_param.AsString() if system_param else "(no system)"
        length_param = p.LookupParameter("Length")
        length = 0.0
        if length_param:
            try:
                length = float(length_param.AsDouble() * 0.3048)
            except:
                length = 0.0
        total_length += length
        rows.append(
            "Name: {}, Type: {}, System: {}, Length: {:.2f} m".format(
                name, typ, system, length
            )
        )
    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} pipes.\n".format(len(pipes))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(rows))
    msg += "\nTotal Length: {:.2f} m".format(total_length)
    return msg


def total_duct_length(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    ducts = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_DuctCurves)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    total_len = 0
    for duct in ducts:
        param = duct.LookupParameter("Length")
        if param:
            try:
                total_len += param.AsDouble()
            except:
                pass
    m = total_len * 0.3048  # Revit units to meters
    return "Total duct length: {:.2f} m".format(m)


def total_pipe_length(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    pipes = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_PipeCurves)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    total_len = 0
    for pipe in pipes:
        param = pipe.LookupParameter("Length")
        if param:
            try:
                total_len += param.AsDouble()
            except:
                pass
    m = total_len * 0.3048
    return "Total pipe length: {:.2f} m".format(m)


def count_ducts(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    ducts = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_DuctCurves)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    return "Total ducts: {}".format(len(ducts))


def delete_all_ducts(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector, Transaction

    ducts = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_DuctCurves)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [d.Id for d in ducts]
    t = Transaction(doc, "Delete all ducts")
    t.Start()
    for i in ids:
        doc.Delete(i)
    t.Commit()
    return "Deleted {} ducts.".format(len(ids))


# --- ELECTRICAL ---
def select_all_lights(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    lights = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_LightingFixtures)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [l.Id for l in lights]
    rows = []
    for l in lights:
        name = get_elem_name(l)
        t = l.Document.GetElement(l.GetTypeId())
        typ = t.Name if (t is not None and hasattr(t, "Name")) else "(no type)"
        rows.append("Name: {}, Type: {}".format(name, typ))
    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} lighting fixtures.\n".format(len(lights))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(rows))
    return msg


def select_all_equip(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    equip = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_ElectricalEquipment)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [e.Id for e in equip]
    rows = []
    for e in equip:
        name = get_elem_name(e)
        t = e.Document.GetElement(e.GetTypeId())
        typ = t.Name if (t is not None and hasattr(t, "Name")) else "(no type)"
        rows.append("Name: {}, Type: {}".format(name, typ))
    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} electrical equipment.\n".format(len(equip))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(rows))
    return msg


def total_cabletray_length(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    trays = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_CableTray)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    total_len = 0
    for tray in trays:
        param = tray.LookupParameter("Length")
        if param:
            try:
                total_len += param.AsDouble()
            except:
                pass
    m = total_len * 0.3048  # Revit units to meters
    return "Total cable tray length: {:.2f} m".format(m)


def select_all_cabletrays(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    trays = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_CableTray)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [t.Id for t in trays]
    rows = []
    total_length = 0
    for t in trays:
        name = get_elem_name(t)
        type_obj = t.Document.GetElement(t.GetTypeId())
        typ = (
            type_obj.Name
            if (type_obj is not None and hasattr(type_obj, "Name"))
            else "(no type)"
        )
        length_param = t.LookupParameter("Length")
        length = 0
        if length_param:
            try:
                length = length_param.AsDouble() * 0.3048
            except:
                pass
        total_length += length
        rows.append("Type: {}, Length: {:.2f} m".format(typ, length))
    uidoc.Selection.SetElementIds(List[DB.ElementId](ids))
    msg = "Selected {} cable trays.\n".format(len(trays))
    msg += "\n".join(rows[:20])
    if len(rows) > 20:
        msg += "\n... (showing first 20 of {})".format(len(rows))
    msg += "\nTotal Length: {:.2f} m".format(total_length)
    return msg


def count_loaded_families(doc, uidoc):
    from Autodesk.Revit.DB import FilteredElementCollector, Family

    fams = FilteredElementCollector(doc).OfClass(Family).ToElements()
    names = [f.Name for f in fams]
    msg = "Loaded families: {}\n".format(
        ", ".join(names[:10]) + (" ..." if len(names) > 10 else "")
    )
    msg += "Total loaded families: {}".format(len(fams))
    return msg


def count_lights(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    lights = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_LightingFixtures)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    return "Total lighting fixtures: {}".format(len(lights))


def delete_all_lights(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector, Transaction

    lights = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_LightingFixtures)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    ids = [l.Id for l in lights]
    t = Transaction(doc, "Delete all lighting fixtures")
    t.Start()
    for i in ids:
        doc.Delete(i)
    t.Commit()
    return "Deleted {} lighting fixtures.".format(len(ids))


# --- GENERAL ---
def get_elem_name(elem):
    try:
        # Prefer the type name if possible
        t = elem.Document.GetElement(elem.GetTypeId())
        if t and hasattr(t, "Name"):
            return t.Name
        if hasattr(elem, "Name"):
            return elem.Name
        # Fallback to ElementId if all else fails
        return "ElementId: {}".format(elem.Id.IntegerValue)
    except Exception as e:
        return "(err)"


def all_parameters_for_category(doc, category):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    elements = (
        FilteredElementCollector(doc)
        .OfCategory(category)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    if not elements:
        return "No elements in category."
    msg = ""
    for elem in elements:
        msg += "\nElement: {} (Id {})\n".format(
            elem.Name if hasattr(elem, "Name") else "(no name)", elem.Id.IntegerValue
        )
        for param in elem.Parameters:
            try:
                pname = param.Definition.Name
                if param.StorageType == DB.StorageType.String:
                    pval = param.AsString()
                elif param.StorageType == DB.StorageType.Double:
                    pval = param.AsDouble()
                elif param.StorageType == DB.StorageType.Integer:
                    pval = param.AsInteger()
                elif param.StorageType == DB.StorageType.ElementId:
                    val = param.AsElementId()
                    pval = val.IntegerValue if val else None
                else:
                    pval = str(param)
                msg += "    {}: {}\n".format(pname, pval)
            except Exception as e:
                msg += "    {}: <error reading>\n".format(param.Definition.Name)
    return msg or "No readable parameters."


def report_all_parameters_of_selection(doc, uidoc):
    selection = uidoc.Selection.GetElementIds()
    if not selection or len(selection) == 0:
        return "No elements selected."
    msg = ""
    for eid in selection:
        elem = doc.GetElement(eid)
        if not elem:
            continue
        msg += "\nElement: {} (Id {})\n".format(
            elem.Name if hasattr(elem, "Name") else "(no name)", eid.IntegerValue
        )
        for param in elem.Parameters:
            try:
                pname = param.Definition.Name
                if param.StorageType == DB.StorageType.String:
                    pval = param.AsString()
                elif param.StorageType == DB.StorageType.Double:
                    pval = param.AsDouble()
                elif param.StorageType == DB.StorageType.Integer:
                    pval = param.AsInteger()
                elif param.StorageType == DB.StorageType.ElementId:
                    val = param.AsElementId()
                    pval = val.IntegerValue if val else None
                else:
                    pval = str(param)
                msg += "    {}: {}\n".format(pname, pval)
            except Exception as e:
                msg += "    {}: <error reading>\n".format(param.Definition.Name)
    return msg or "No readable parameters."


def report_phases_of_selection(doc, uidoc):
    selection = uidoc.Selection.GetElementIds()
    if not selection or len(selection) == 0:
        return "No elements selected."
    msg = ""
    for eid in selection:
        elem = doc.GetElement(eid)
        if not elem:
            continue
        phase_created = None
        phase_demolished = None
        if hasattr(elem, "CreatedPhaseId"):
            pc = elem.CreatedPhaseId
            pd = elem.DemolishedPhaseId
            phase_created = doc.GetElement(pc).Name if pc.IntegerValue > 0 else "None"
            phase_demolished = (
                doc.GetElement(pd).Name if pd and pd.IntegerValue > 0 else "None"
            )
        msg += "Element: {} (Id {})\n".format(
            elem.Name if hasattr(elem, "Name") else "(no name)", eid.IntegerValue
        )
        msg += "    Created in phase: {}\n".format(phase_created)
        msg += "    Demolished in phase: {}\n".format(phase_demolished)
    return msg or "No readable phase data."


def list_all_phases(doc, uidoc):
    from Autodesk.Revit.DB import FilteredElementCollector, Phase

    phases = FilteredElementCollector(doc).OfClass(Phase).ToElements()
    if not phases:
        return "No phases found."
    msg = "Phases in project:\n"
    for p in phases:
        msg += "    {} (Id: {})\n".format(p.Name, p.Id.IntegerValue)
    return msg


def tag_selected_elements(doc, uidoc):
    from Autodesk.Revit.DB import Transaction, XYZ

    eids = uidoc.Selection.GetElementIds()
    if not eids or len(eids) == 0:
        return "No elements selected."
    t = Transaction(doc, "Tag elements")
    t.Start()
    count = 0
    for eid in eids:
        elem = doc.GetElement(eid)
        # Try to tag if taggable (Rooms, Walls, Doors, Windows)
        pt = None
        loc = getattr(elem, "Location", None)
        if hasattr(loc, "Point"):
            pt = loc.Point
        elif hasattr(loc, "Curve"):
            pt = loc.Curve.Evaluate(0.5, True)
        # You can expand: check element category for what tag to create
        if pt:
            try:
                doc.Create.NewTag(
                    None,
                    elem,
                    False,
                    DB.TagMode.TM_ADDBY_CATEGORY,
                    DB.TagOrientation.Horizontal,
                    pt,
                )
                count += 1
            except:
                pass
    t.Commit()
    return "Tagged {} elements.".format(count)


def count_all_sheets(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    sheets = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Sheets)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    names = [
        s.LookupParameter("Sheet Number").AsString()
        + " "
        + s.LookupParameter("Sheet Name").AsString()
        for s in sheets
        if s.LookupParameter("Sheet Number") and s.LookupParameter("Sheet Name")
    ]
    msg = "Total sheets: {}\n".format(len(sheets))
    msg += "Sheets: {}\n".format(
        ", ".join(names[:10]) + (" ..." if len(names) > 10 else "")
    )
    return msg


def list_all_sheets(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

    sheets = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Sheets)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    msg = "Sheets:\n"
    for s in sheets:
        num = (
            s.LookupParameter("Sheet Number").AsString()
            if s.LookupParameter("Sheet Number")
            else "?"
        )
        name = (
            s.LookupParameter("Sheet Name").AsString()
            if s.LookupParameter("Sheet Name")
            else "?"
        )
        msg += "    {} - {}\n".format(num, name)
    return msg


def count_all_views(doc, uidoc):
    from Autodesk.Revit.DB import View, FilteredElementCollector

    views = FilteredElementCollector(doc).OfClass(View).ToElements()
    names = [v.Name for v in views if hasattr(v, "Name")]
    msg = "Total views: {}\n".format(len(views))
    msg += "View names: {}\n".format(
        ", ".join(names[:10]) + (" ..." if len(names) > 10 else "")
    )
    return msg


def list_all_views(doc, uidoc):
    from Autodesk.Revit.DB import View, FilteredElementCollector

    views = FilteredElementCollector(doc).OfClass(View).ToElements()
    msg = "Views:\n"
    for v in views:
        msg += "    {}\n".format(v.Name)
    return msg


def list_all_families(doc, uidoc):
    from Autodesk.Revit.DB import Family, FilteredElementCollector

    fams = FilteredElementCollector(doc).OfClass(Family).ToElements()
    msg = "Families:\n"
    for f in fams:
        msg += "    {}\n".format(f.Name)
    return msg


def list_all_levels(doc, uidoc):
    from Autodesk.Revit.DB import Level, FilteredElementCollector

    lvls = FilteredElementCollector(doc).OfClass(Level).ToElements()
    msg = "Levels:\n"
    for l in lvls:
        msg += "    {} (Elevation: {:.2f} m)\n".format(l.Name, l.Elevation * 0.3048)
    return msg


def export_schedule_names(doc, uidoc):
    from Autodesk.Revit.DB import ViewSchedule, FilteredElementCollector

    schedules = FilteredElementCollector(doc).OfClass(ViewSchedule).ToElements()
    names = [sch.Name for sch in schedules]
    msg = "Schedules in project: {}\n".format(
        ", ".join(names[:10]) + (" ..." if len(names) > 10 else "")
    )
    msg += "Total schedules: {}".format(len(schedules))
    return msg


def export_all_schedule_data(doc, uidoc):
    from Autodesk.Revit.DB import ViewSchedule, FilteredElementCollector
    import codecs

    schedules = FilteredElementCollector(doc).OfClass(ViewSchedule).ToElements()
    output = []
    for sch in schedules:
        output.append("Schedule: {}".format(sch.Name))
        # Optionally: Export fields, rows, etc!
    with codecs.open(r"C:\\exported_schedules.txt", "w", "utf-8") as f:
        f.write("\n".join(output))
    return "Exported {} schedule names to C:\\exported_schedules.txt".format(
        len(schedules)
    )


def clash_check_category_vs_category(doc, cat1, cat2, tol=0.01):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector, Outline

    elements1 = (
        FilteredElementCollector(doc)
        .OfCategory(cat1)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    elements2 = (
        FilteredElementCollector(doc)
        .OfCategory(cat2)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    clashes = []
    for el1 in elements1:
        bb1 = el1.get_BoundingBox(None)
        if not bb1:
            continue
        outline1 = Outline(bb1.Min, bb1.Max)
        for el2 in elements2:
            bb2 = el2.get_BoundingBox(None)
            if not bb2:
                continue
            outline2 = Outline(bb2.Min, bb2.Max)
            if outline1.Intersects(outline2, tol):
                clashes.append((el1.Id.IntegerValue, el2.Id.IntegerValue))
    return clashes


def check_clashes_walls_vs_columns(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory

    clashes = clash_check_category_vs_category(
        doc, BuiltInCategory.OST_Walls, BuiltInCategory.OST_StructuralColumns
    )
    msg = "Wall-Column clashes found: {}\n".format(len(clashes))
    if len(clashes) > 0:
        msg += "Sample clashes (wallId,columnId): {}\n".format(
            ", ".join(str(pair) for pair in clashes[:10])
        )
    return msg


def check_clashes_ducts_vs_beams(doc, uidoc):
    from Autodesk.Revit.DB import BuiltInCategory

    clashes = clash_check_category_vs_category(
        doc, BuiltInCategory.OST_DuctCurves, BuiltInCategory.OST_StructuralFraming
    )
    return "Duct-Beam clashes found: {}".format(len(clashes))


def model_health_check(doc, uidoc):
    report = []
    from Autodesk.Revit.DB import (
        FilteredElementCollector,
        BuiltInCategory,
        View,
        Family,
        Phase,
        ViewSchedule,
        ElementType,
        Level,
        ViewSheet,
        Group,
        Grid,
        ReferencePlane,
        ImportInstance,
        RevitLinkInstance,
        DesignOption,  # (NO DesignOptionSet!)
        ParameterFilterElement,
        View3D,
        ViewPlan,
        ViewDrafting,
        WorksharingUtils,
        ProjectLocation,
        Workset,
    )
    import datetime
    import math

    errors = []
    warnings = []
    score = 100

    def section(title):
        report.append("\n== {} ==".format(title))

    def item(txt):
        report.append(" - {}".format(txt))

    # File Info
    section("File Info")
    try:
        file_path = doc.PathName or "(unsaved)"
        item("File: {}".format(file_path))
        file_size = (
            os.path.getsize(file_path) / (1024 * 1024)
            if os.path.exists(file_path)
            else None
        )
        if file_size:
            item("Size: {:.1f} MB".format(file_size))
    except:
        item("File size: N/A")

    # Worksharing Info
    section("Worksharing")
    try:
        is_workshared = WorksharingUtils.IsWorkshared(doc)
        item("Workshared: {}".format("Yes" if is_workshared else "No"))
        if is_workshared:
            item("Central Path: {}".format(WorksharingUtils.GetCentralServerPath(doc)))
            try:
                item(
                    "Worksets: {}".format(
                        len(list(FilteredElementCollector(doc).OfClass(Workset)))
                    )
                )
            except:
                item("Worksets: N/A")
    except:
        item("N/A")

    # Project Info
    section("Project Info")
    try:
        pi = doc.ProjectInformation
        item("Project Name: {}".format(pi.Name))
        item("Project Number: {}".format(pi.Number))
    except:
        item("N/A")

    # Basic Counts
    section("Main Element Counts")

    def count(cat):
        return len(
            list(
                FilteredElementCollector(doc)
                .OfCategory(cat)
                .WhereElementIsNotElementType()
            )
        )

    main_cats = [
        ("Walls", BuiltInCategory.OST_Walls),
        ("Columns", BuiltInCategory.OST_StructuralColumns),
        ("Beams", BuiltInCategory.OST_StructuralFraming),
        ("Floors", BuiltInCategory.OST_Floors),
        ("Roofs", BuiltInCategory.OST_Roofs),
        ("Doors", BuiltInCategory.OST_Doors),
        ("Windows", BuiltInCategory.OST_Windows),
        ("Rooms", BuiltInCategory.OST_Rooms),
        ("Areas", BuiltInCategory.OST_Areas),
        ("Grids", BuiltInCategory.OST_Grids),
        ("Ref Planes", BuiltInCategory.OST_CLines),
        ("Model Groups", BuiltInCategory.OST_IOSModelGroups),
        ("Curtain Panels", BuiltInCategory.OST_CurtainWallPanels),
        ("Rebars", BuiltInCategory.OST_Rebar),
        ("Stairs", BuiltInCategory.OST_Stairs),
        ("Ducts", BuiltInCategory.OST_DuctCurves),
        ("Pipes", BuiltInCategory.OST_PipeCurves),
        ("Sheets", BuiltInCategory.OST_Sheets),
    ]
    for name, cat in main_cats:
        c = count(cat)
        item("{}: {}".format(name, c))
        if name in ["Walls", "Floors", "Roofs"] and c > 2000:
            warnings.append("Too many {} ({})".format(name, c))
            score -= 2

    # Families/Types
    fams = list(FilteredElementCollector(doc).OfClass(Family))
    fam_types = list(FilteredElementCollector(doc).OfClass(ElementType))
    item("Families: {}".format(len(fams)))
    item("Element Types: {}".format(len(fam_types)))

    # Views/Schedules/Phases/Levels
    section("Views, Schedules, Levels, Phases")
    item("Views: {}".format(len(list(FilteredElementCollector(doc).OfClass(View)))))
    item(
        "3D Views: {}".format(len(list(FilteredElementCollector(doc).OfClass(View3D))))
    )
    item(
        "Plan Views: {}".format(
            len(list(FilteredElementCollector(doc).OfClass(ViewPlan)))
        )
    )
    item(
        "Drafting Views: {}".format(
            len(list(FilteredElementCollector(doc).OfClass(ViewDrafting)))
        )
    )
    sheets = list(FilteredElementCollector(doc).OfClass(ViewSheet))
    item("Sheets: {}".format(len(sheets)))
    schedules = list(FilteredElementCollector(doc).OfClass(ViewSchedule))
    item("Schedules: {}".format(len(schedules)))
    levels = list(FilteredElementCollector(doc).OfClass(Level))
    item("Levels: {}".format(len(levels)))
    phases = list(FilteredElementCollector(doc).OfClass(Phase))
    item("Phases: {}".format(len(phases)))
    view_templates = [
        v
        for v in FilteredElementCollector(doc).OfClass(View)
        if hasattr(v, "IsTemplate") and v.IsTemplate
    ]
    item("View Templates: {}".format(len(view_templates)))

    # Unplaced/Empty/Problematic
    section("Potential Problems")
    unplaced_rooms = [
        r
        for r in FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Rooms)
        .WhereElementIsNotElementType()
        if hasattr(r, "Area") and r.Area == 0
    ]
    item("Unplaced Rooms: {}".format(len(unplaced_rooms)))
    if unplaced_rooms:
        warnings.append("Unplaced rooms present")
        score -= 2
    unplaced_areas = [
        a
        for a in FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Areas)
        .WhereElementIsNotElementType()
        if hasattr(a, "Area") and a.Area == 0
    ]
    item("Unplaced Areas: {}".format(len(unplaced_areas)))
    unused_families = [f for f in fams if not list(f.GetFamilySymbolIds())]
    item("Families with No Types: {}".format(len(unused_families)))
    # unused_levels = [
    #     l for l in levels if not list(l.FindInserts(True, True, True, True))
    # ]
    # item("Unused Levels: {}".format(len(unused_levels)))

    # Empty Views, Sheets without views
    item("Unused Levels: (not checked)")
    empty_views = [
        v
        for v in FilteredElementCollector(doc).OfClass(View)
        if hasattr(v, "GetDependentElements")
        and len(list(v.GetDependentElements(None))) == 0
        and not v.IsTemplate
    ]
    item("Empty Views: {}".format(len(empty_views)))
    empty_sheets = [s for s in sheets if len(s.GetAllPlacedViews()) == 0]
    item("Sheets Without Views: {}".format(len(empty_sheets)))
    if empty_sheets:
        score -= 2

    # Outdated/Unloaded Links
    section("Links & Imports")
    links = list(FilteredElementCollector(doc).OfClass(RevitLinkInstance))
    item("Linked RVT: {}".format(len(links)))
    cad_imports = list(FilteredElementCollector(doc).OfClass(ImportInstance))
    item("Linked/Imported CAD: {}".format(len(cad_imports)))
    outdated_links = [l for l in links if hasattr(l, "IsLoaded") and not l.IsLoaded]
    item("Outdated/Unloaded RVT Links: {}".format(len(outdated_links)))
    if outdated_links:
        score -= 3

    # Shared Coordinates
    locations = list(FilteredElementCollector(doc).OfClass(ProjectLocation))
    shared_coords = any(
        [getattr(loc, "AreSharedCoordinatesInitialized", False) for loc in locations]
    )
    item("Shared Coordinates: {}".format("Yes" if shared_coords else "No"))
    if not shared_coords:
        warnings.append("Shared coordinates not set")

    # Model Groups
    groups = list(FilteredElementCollector(doc).OfClass(Group))
    item("Groups: {}".format(len(groups)))

    # Parameter Filters
    param_filters = list(FilteredElementCollector(doc).OfClass(ParameterFilterElement))
    item("Parameter Filters: {}".format(len(param_filters)))

    # Design Options
    try:
        optMgr = doc.GetDesignOptionManager()
        sets = [optMgr.GetOptionSet(i) for i in range(optMgr.NumberOfOptionSets)]
        item("Design Option Sets: {}".format(len(sets)))
        dos = list(FilteredElementCollector(doc).OfClass(DB.DesignOption))
        item("Design Options: {}".format(len(dos)))
    except:
        item("Design Option Sets: N/A")
        item("Design Options: N/A")

    # Last Saved
    try:
        from System import DateTime

        save_time = doc.LastSavedTime if hasattr(doc, "LastSavedTime") else None
        if save_time:
            if isinstance(save_time, DateTime):
                save_time = save_time.ToLocalTime()
            item("Last Saved: {}".format(save_time))
    except:
        item("Last Saved: (N/A)")

    # Warnings
    section("Warnings")
    try:
        doc_warnings = doc.GetWarnings()
        n_warn = doc_warnings.Count
        item("Total Warnings: {}".format(n_warn))
        # Top 10 warning types summary
        warn_types = {}
        for w in doc_warnings:
            wt = w.GetDescriptionText()
            if wt in warn_types:
                warn_types[wt] += 1
            else:
                warn_types[wt] = 1
        if warn_types:
            for t, c in sorted(warn_types.items(), key=lambda x: -x[1])[:10]:
                item("Warning: {} ({}x)".format(t, c))
        if n_warn > 0:
            score -= min(10, n_warn // 50)  # Penalty per 50 warnings
    except:
        item("Could not read warnings.")

    # Duplicate Mark Checks
    section("Data Quality Checks")
    marks = {}
    duplicates = set()
    for el in FilteredElementCollector(doc).WhereElementIsNotElementType():
        try:
            mark = (
                el.LookupParameter("Mark").AsString()
                if el.LookupParameter("Mark")
                else None
            )
            if mark and mark not in ["", None]:
                if mark in marks:
                    duplicates.add(mark)
                else:
                    marks[mark] = 1
        except:
            continue
    item(
        "Duplicate Marks: {}".format(
            ", ".join(list(duplicates)) if duplicates else "None"
        )
    )
    if duplicates:
        score -= 3

    # Large Elements
    section("Largest Elements")
    # Walls, Floors, Roofs by volume
    try:
        biggest_walls = sorted(
            [
                w
                for w in FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Walls)
                .WhereElementIsNotElementType()
                if w.LookupParameter("Volume")
            ],
            key=lambda x: x.LookupParameter("Volume").AsDouble(),
            reverse=True,
        )[:3]
        for w in biggest_walls:
            v = w.LookupParameter("Volume").AsDouble() * 0.0283168
            item(
                "Big Wall: '{}' {:.2f} m³".format(
                    getattr(w, "Name", w.Id.IntegerValue), v
                )
            )
    except:
        pass
    try:
        biggest_floors = sorted(
            [
                f
                for f in FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Floors)
                .WhereElementIsNotElementType()
                if f.LookupParameter("Volume")
            ],
            key=lambda x: x.LookupParameter("Volume").AsDouble(),
            reverse=True,
        )[:3]
        for f in biggest_floors:
            v = f.LookupParameter("Volume").AsDouble() * 0.0283168
            item(
                "Big Floor: '{}' {:.2f} m³".format(
                    getattr(f, "Name", f.Id.IntegerValue), v
                )
            )
    except:
        pass

    # Families/Types Most Common
    section("Most Common Families / Types")
    fam_count = {}
    for el in FilteredElementCollector(doc).WhereElementIsNotElementType():
        try:
            t = el.Document.GetElement(el.GetTypeId())
            n = t.Name if t else "(unknown)"
            fam_count[n] = fam_count.get(n, 0) + 1
        except:
            continue
    for fam, cnt in sorted(fam_count.items(), key=lambda x: -x[1])[:5]:
        item("{}: {} instances".format(fam, cnt))

    # Schedules with no rows
    empty_schedules = []
    for s in schedules:
        try:
            if s.Definition.GetTableData().GetSectionData(0).NumberOfRows == 0:
                empty_schedules.append(s.Name)
        except:
            continue
    if empty_schedules:
        section("Empty Schedules")
        for n in empty_schedules:
            item("Empty schedule: {}".format(n))

    # Views not on sheets
    views_not_on_sheet = []
    for v in FilteredElementCollector(doc).OfClass(View):
        if (
            not v.IsTemplate
            and hasattr(v, "CanBePrinted")
            and v.CanBePrinted
            and v.ViewType.ToString() not in ["DrawingSheet", "Schedule"]
        ):
            placed = False
            for s in sheets:
                if v.Id in s.GetAllPlacedViews():
                    placed = True
                    break
            if not placed:
                views_not_on_sheet.append(v.Name)
    section("Views Not On Sheets")
    item("Views not on sheets: {}".format(len(views_not_on_sheet)))

    # Health Score
    section("Health Score")
    if score > 90:
        status = "Excellent"
    elif score > 75:
        status = "Good"
    elif score > 60:
        status = "Warning"
    else:
        status = "Critical"
    item("Health Score: {} ({})".format(score, status))

    # Warnings/Errors
    if errors:
        section("Critical Errors")
        for e in errors:
            item(e)
    if warnings:
        section("Warnings")
        for w in warnings:
            item(w)

    section("End of Health Check")
    return "\n".join(report)


def super_select(doc, uidoc, categories):
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    from System.Collections.Generic import List

    # Map string to BuiltInCategory safely
    cat_map = {
        "walls": BuiltInCategory.OST_Walls,
        "columns": BuiltInCategory.OST_StructuralColumns,
        "ceilings": BuiltInCategory.OST_Ceilings,
        "beams": BuiltInCategory.OST_StructuralFraming,
        "foundations": BuiltInCategory.OST_StructuralFoundation,
        "floors": BuiltInCategory.OST_Floors,
        "windows": BuiltInCategory.OST_Windows,
        "doors": BuiltInCategory.OST_Doors,
        "rebars": BuiltInCategory.OST_Rebar,
        "roofs": BuiltInCategory.OST_Roofs,
        "ducts": BuiltInCategory.OST_DuctCurves,
        "pipes": BuiltInCategory.OST_PipeCurves,
        # Add more as needed!
    }
    selected_ids = []
    summary = []
    for cat in categories:
        cat = cat.strip().lower()
        if cat not in cat_map:
            summary.append("Category not found: {}".format(cat))
            continue
        elems = (
            FilteredElementCollector(doc)
            .OfCategory(cat_map[cat])
            .WhereElementIsNotElementType()
            .ToElements()
        )
        ids = [e.Id for e in elems]
        selected_ids.extend(ids)
        summary.append("Selected {} {}.".format(len(elems), cat))
    # Set the selection in Revit
    if selected_ids:
        uidoc.Selection.SetElementIds(List[DB.ElementId](selected_ids))
    return "\n".join(summary)


# Add more public command functions as needed!
MODELMIND_COMMANDS = [
    "select all columns",
    "select all walls",
    "select all floors",
    "select all ceilings",
    "select all roofs",
    "select all beams",
    "select all foundations",
    "select all rebars",
    "count rebars",
    "count columns",
    "count walls",
    "count floors",
    "count ceilings",
    "count roofs",
    "count ducts",
    "count lights",
    "total structural volume",
    "select all windows",
    "select all doors",
    "total room area",
    "delete all doors",
    "delete all columns",
    "delete all walls",
    "delete all ceilings",
    "delete all roofs",
    "delete all ducts",
    "delete all lights",
    "select all ducts",
    "select all pipes",
    "total duct length",
    "total pipe length",
    "total ceiling area and volume",
    "total roof area and volume",
    "select all lights",
    "select all electrical equipment",
    "total cable tray length",
    "count all sheets",
    "count all views",
    "export schedule names",
    "export all schedule data",
    "clash check",
    "report parameters",
    "report phases",
    "material takeoff wall",
    "material takeoff floor",
    "material takeoff columns",
    "material takeoff beams",
    "material takeoff roofs",
    "material takeoff stairs",
    "material takeoff curtain panel",
    "material takeoff rebar",
    "tag selection",
    "count loaded families",
    "all parameters for walls",
    "all parameters for rooms",
    "list all phases",
    "list all sheets",
    "list all views",
    "list all families",
    "list all levels",
    "health check",
    "super-select walls, columns, beams",  # add any combination you like!
    # Add more as you invent them!
]


def handle_public_command(prompt, doc, uidoc):
    p = prompt.lower()
    if p.startswith("super-select"):
        # Example: "super-select walls, columns, beams"
        cats = re.findall(r"super-select\s+(.*)", p)
        if cats:
            cat_list = [c.strip() for c in cats[0].split(",")]
            return super_select(doc, uidoc, cat_list)
        else:
            return "Usage: super-select walls, columns, beams"
    if "select all columns" in p:
        return select_all_columns(doc, uidoc)
    if "select all walls" in p:
        return select_all_walls(doc, uidoc)
    if "select all floors" in p:
        return select_all_floors(doc, uidoc)
    if "select all ceilings" in p:
        return select_all_ceilings(doc, uidoc)
    if "select all roofs" in p:
        return select_all_roofs(doc, uidoc)
    if "select all beams" in p:
        return select_all_beams(doc, uidoc)
    if "select all foundations" in p:
        return select_all_foundations(doc, uidoc)
    if "select all rebars" in p:
        return select_all_rebars(doc, uidoc)
    if "select all cable trays" in p:
        return select_all_cabletrays(doc, uidoc)
    if "count rebars" in p:
        return count_rebars(doc, uidoc)
    if "count columns" in p:
        return count_columns(doc, uidoc)
    if "count walls" in p:
        return count_walls(doc, uidoc)
    if "count floors" in p:
        return count_floors(doc, uidoc)
    if "count ceilings" in p:
        return count_ceilings(doc, uidoc)
    if "count roofs" in p:
        return count_roofs(doc, uidoc)
    if "count ducts" in p:
        return count_ducts(doc, uidoc)
    if "count lights" in p:
        return count_lights(doc, uidoc)
    if "total structural volume" in p:
        return total_structural_volume(doc, uidoc)
    if "select all windows" in p:
        return select_all_windows(doc, uidoc)
    if "select all doors" in p:
        return select_all_doors(doc, uidoc)
    if "total room area" in p:
        return total_room_area(doc, uidoc)
    if "delete all doors" in p:
        return delete_all_doors(doc, uidoc)
    if "delete all columns" in p:
        return delete_all_columns(doc, uidoc)
    if "delete all walls" in p:
        return delete_all_walls(doc, uidoc)
    if "delete all ceilings" in p:
        return delete_all_ceilings(doc, uidoc)
    if "delete all roofs" in p:
        return delete_all_roofs(doc, uidoc)
    if "delete all ducts" in p:
        return delete_all_ducts(doc, uidoc)
    if "delete all lights" in p:
        return delete_all_lights(doc, uidoc)
    if "select all ducts" in p:
        return select_all_ducts(doc, uidoc)
    if "select all pipes" in p:
        return select_all_pipes(doc, uidoc)
    if "total duct length" in p:
        return total_duct_length(doc, uidoc)
    if "total pipe length" in p:
        return total_pipe_length(doc, uidoc)
    if "select all lights" in p:
        return select_all_lights(doc, uidoc)
    if "select all electrical equipment" in p or "select all equip" in p:
        return select_all_equip(doc, uidoc)
    if "total cable tray length" in p:
        return total_cabletray_length(doc, uidoc)
    if "total ceiling area and volume" in p:
        return total_ceiling_area_volume(doc, uidoc)
    if "total roof area and volume" in p:
        return total_roof_area_volume(doc, uidoc)
    if "count all sheets" in p:
        return count_all_sheets(doc, uidoc)
    if "count all views" in p:
        return count_all_views(doc, uidoc)
    if "export schedule names" in p:
        return export_schedule_names(doc, uidoc)
    if "export all schedule data" in p:
        return export_all_schedule_data(doc, uidoc)
    if "clash check" in p or "check clashes" in p:
        return check_clashes_walls_vs_columns(doc, uidoc)
    if "clash check walls columns" in p:
        return check_clashes_walls_vs_columns(doc, uidoc)
    if "clash check ducts beams" in p:
        return check_clashes_ducts_vs_beams(doc, uidoc)
    if "report parameters" in p or "list parameters" in p:
        return report_all_parameters_of_selection(doc, uidoc)
    if "report phases" in p or "phase info" in p:
        return report_phases_of_selection(doc, uidoc)
    if "material takeoff wall" in p:
        return material_takeoff_walls(doc, uidoc)
    if "material takeoff floor" in p:
        return material_takeoff_floors(doc, uidoc)
    if "material takeoff columns" in p:
        return material_takeoff_columns(doc, uidoc)
    if "material takeoff beams" in p:
        return material_takeoff_beams(doc, uidoc)
    if "material takeoff roofs" in p:
        return material_takeoff_roofs(doc, uidoc)
    if "material takeoff stairs" in p:
        return material_takeoff_stairs(doc, uidoc)
    if "material takeoff curtain panel" in p:
        return material_takeoff_curtainpanels(doc, uidoc)
    if "material takeoff rebar" in p:
        return material_takeoff_rebar(doc, uidoc)
    if "tag selection" in p or "tag selected" in p:
        return tag_selected_elements(doc, uidoc)
    if "count loaded families" in p:
        return count_loaded_families(doc, uidoc)
    if "all parameters for walls" in p:
        return all_parameters_for_category(doc, DB.BuiltInCategory.OST_Walls)
    if "all parameters for rooms" in p:
        return all_parameters_for_category(doc, DB.BuiltInCategory.OST_Rooms)
    if "all parameters for" in p and "category" in p:
        # Parse out BuiltInCategory from user input
        # e.g. "all parameters for category OST_Floors"
        cat_name = p.split("category")[-1].strip()
        try:
            category = getattr(DB.BuiltInCategory, cat_name)
            return all_parameters_for_category(doc, category)
        except:
            return "Unknown category: {}".format(cat_name)
    if "list all phases" in p or "show phases" in p:
        return list_all_phases(doc, uidoc)
    if "list all sheets" in p:
        return list_all_sheets(doc, uidoc)
    if "list all views" in p:
        return list_all_views(doc, uidoc)
    if "list all families" in p:
        return list_all_families(doc, uidoc)
    if "list all levels" in p:
        return list_all_levels(doc, uidoc)
    if "health check" in p or "model audit" in p:
        return model_health_check(doc, uidoc)

    # Add more keyword->function mappings here
    return None  # No public command matched


def sanitize_llm_code(code):
    """
    Cleans LLM-generated code for safe execution in the Revit pyRevit context.
    - Removes extra imports and context assignments
    - Keeps only actual command logic
    """
    lines = code.splitlines()
    keep = []
    skip_prefixes = [
        "import DB",  # LLM import, not needed
        "import revit",  # Unneeded imports
        "from pyrevit",  # Unneeded imports
        "uidoc =",  # LLM context assignment
        "doc =",  # LLM context assignment
        "DB.Application.",  # Not valid in IronPython
        "DB.ActiveUIDocument",  # Not valid as assignment
        "#",  # Usually explanations, skip
        "import Autodesk.",  # Also not needed
        "import clr",  # Already handled
    ]
    for line in lines:
        l = line.strip()
        # Remove lines that are just triple backticks or language markers
        if l.startswith("```"):
            continue
        # Remove unwanted lines
        if any(l.startswith(prefix) for prefix in skip_prefixes):
            continue
        # Remove empty lines (optional)
        if l == "":
            continue
        keep.append(line)
    return "\n".join(keep)


def llm_output_safety_filter(code):
    banned_patterns = [
        "doc.Database",
        "doc.Levels",
        "NewGeometryReference",
        "UIDoc.ActiveDoc",
        "DB.ActiveUIDocument",
        "UIApplication",
        "revitUIApplication",
        "Dynamo",
        "Rhino",
        "import revit",
        "SetCamera",
        "GetInput",
    ]
    for pattern in banned_patterns:
        if pattern in code:
            return "# Not possible with current API"
    return code


def run_code_in_revit(code, doc, uidoc):
    # WARNING: Executing code from a string can be dangerous!
    # This should only be done in a trusted context, never with untrusted user input.
    local_vars = {"doc": doc, "uidoc": uidoc, "DB": DB}
    try:
        exec(code, globals(), local_vars)
        return "Code executed successfully."
    except Exception as e:
        return "Error executing code: {}".format(str(e))


# === WPF Window Logic ===


class OllamaAIChat(forms.WPFWindow):
    def __init__(self, xaml_path):
        forms.WPFWindow.__init__(self, xaml_path)
        self.model = DEFAULT_MODEL
        self.populate_model_selector()
        self.ModelSelector.SelectionChanged += self.on_model_selected
        self.refresh_model_info()

        # === Ollama Chat tab
        self.SendButton.Click += self.on_send_chat
        # === ModelMind tab
        self.ModelMindSendButton.Click += self.on_modelmind_send
        # === Top
        self.UpgradeButton.Click += self.on_upgrade_model
        self.CloseButton.Click += self.on_close
        self.ApproveCodeButton.Click += self.on_approve_code
        self.pending_ai_code = None  # Store pending code safely
        self.populate_prompt_tree()
        self.ModelMindInput.KeyDown += self.on_modelmindinput_keydown
        self.PromptTree.MouseDoubleClick += self.on_prompt_tree_doubleclick
        self.PromptTree.KeyDown += self.on_prompt_tree_keydown
        self.ModelMindInput.TextChanged += self.on_modelmind_input_changed

        if hasattr(self, "HeaderBar"):
            self.HeaderBar.MouseLeftButtonDown += self._on_header_drag

    def _set_thinking(self, text):
        try:
            self.ThinkingLabel.Text = text
        except:
            try:
                self.ThinkingLabel.Content = text
            except:
                pass

    def show_busy(self):
        self.BusyBar.Visibility = System.Windows.Visibility.Visible
        self.ThinkingLabel.Visibility = System.Windows.Visibility.Visible

    def hide_busy(self):
        self.BusyBar.Visibility = System.Windows.Visibility.Collapsed
        self.ThinkingLabel.Visibility = System.Windows.Visibility.Collapsed

    def populate_prompt_list(self):
        self.PromptListBox.Items.Clear()
        for cmd in MODELMIND_COMMANDS:
            self.PromptListBox.Items.Add(cmd)

    def populate_prompt_tree(self, filter_text=None):
        # Build (or rebuild) the TreeView with optional filter
        from System.Windows.Controls import TreeViewItem

        ft = (filter_text or "").lower()
        self.PromptTree.Items.Clear()

        for cat, cmds in self.CATEGORY_PROMPTS.items():
            # filter children by text if any
            child_cmds = [c for c in cmds if ft in c.lower()] if ft else list(cmds)
            if not child_cmds:
                continue

            cat_item = TreeViewItem()
            cat_item.Header = cat
            cat_item.IsExpanded = bool(ft)  # auto-expand when filtering

            for cmd in child_cmds:
                leaf = TreeViewItem()
                leaf.Header = cmd
                leaf.Tag = cmd  # store the command text
                cat_item.Items.Add(leaf)

            self.PromptTree.Items.Add(cat_item)

    def on_prompt_tree_doubleclick(self, sender, args):
        # Put selected leaf command into the input box
        sel = self.PromptTree.SelectedItem
        try:
            # sel is a TreeViewItem; only act on leaves
            if sel is not None and hasattr(sel, "Items") and sel.Items.Count == 0:
                cmd = sel.Tag if hasattr(sel, "Tag") else None
                if cmd:
                    self.ModelMindInput.Text = cmd
                    self.ModelMindInput.CaretIndex = len(self.ModelMindInput.Text)
                    self.ModelMindInput.Focus()
        except:
            pass

    def on_prompt_tree_keydown(self, sender, args):
        import System.Windows.Input as wpfInput

        if args.Key in (wpfInput.Key.Enter, wpfInput.Key.Tab):
            sel = self.PromptTree.SelectedItem
            try:
                if sel is not None and hasattr(sel, "Items") and sel.Items.Count == 0:
                    cmd = sel.Tag if hasattr(sel, "Tag") else None
                    if cmd:
                        self.ModelMindInput.Text = cmd
                        self.ModelMindInput.CaretIndex = len(self.ModelMindInput.Text)
                        self.ModelMindInput.Focus()
                        args.Handled = True
            except:
                pass

    def filter_prompt_tree(self, text):
        # simple rebuild with filter
        self.populate_prompt_tree(filter_text=text)

    def on_modelmind_input_changed(self, sender, args):
        typed = self.ModelMindInput.Text or ""
        self.filter_prompt_tree(typed)

    CATEGORY_PROMPTS = {
        "Select All": [
            "select all columns",
            "select all walls",
            "select all floors",
            "select all ceilings",
            "select all roofs",
            "select all beams",
            "select all foundations",
            "select all rebars",
            "select all windows",
            "select all doors",
            "select all ducts",
            "select all pipes",
            "select all lights",
            "select all electrical equipment",
            "select all cable trays",  # NEW: we'll route this below
        ],
        "Count": [
            "count rebars",
            "count columns",
            "count walls",
            "count floors",
            "count ceilings",
            "count roofs",
            "count ducts",
            "count lights",
            "count all sheets",
            "count all views",
            "count loaded families",
        ],
        "Delete": [
            "delete all doors",
            "delete all columns",
            "delete all walls",
            "delete all ceilings",
            "delete all roofs",
            "delete all ducts",
            "delete all lights",
        ],
        "Totals": [
            "total structural volume",
            "total room area",
            "total duct length",
            "total pipe length",
            "total cable tray length",
            "total ceiling area and volume",
            "total roof area and volume",
        ],
        "Materials": [
            "material takeoff wall",
            "material takeoff floor",
            "material takeoff columns",
            "material takeoff beams",
            "material takeoff roofs",
            "material takeoff stairs",
            "material takeoff curtain panel",
            "material takeoff rebar",
        ],
        "Clash Check": [
            "clash check",
            "clash check walls columns",
            "clash check ducts beams",
        ],
        "Reports": [
            "report parameters",
            "report phases",
            "export schedule names",
            "export all schedule data",
            "health check",
        ],
        "Lists": [
            "list all phases",
            "list all sheets",
            "list all views",
            "list all families",
            "list all levels",
        ],
        "Tags / Tools": [
            "tag selection",
            "super-select walls, columns, beams",
        ],
    }

    def on_modelmindinput_keydown(self, sender, args):
        import System.Windows.Input as wpfInput

        if args.Key == wpfInput.Key.Enter:
            self.on_modelmind_send(sender, args)
            args.Handled = True

    def on_prompt_listbox_doubleclick(self, sender, args):
        if self.PromptListBox.SelectedItem:
            self.ModelMindInput.Text = self.PromptListBox.SelectedItem

    def on_prompt_listbox_keydown(self, sender, args):
        import System.Windows.Input as wpfInput

        # Check if user pressed Enter or Tab
        if args.Key == wpfInput.Key.Enter or args.Key == wpfInput.Key.Tab:
            if self.PromptListBox.SelectedItem:
                self.ModelMindInput.Text = self.PromptListBox.SelectedItem
                self.ModelMindInput.CaretIndex = len(self.ModelMindInput.Text)
                self.ModelMindInput.Focus()  # Put focus back to input box
                args.Handled = True  # Stop further event processing

    def populate_model_selector(self):
        models = get_all_models()
        self.ModelSelector.Items.Clear()
        for m in models:
            self.ModelSelector.Items.Add(m)
        if self.model in models:
            self.ModelSelector.SelectedItem = self.model

    def on_model_selected(self, sender, args):
        selected = self.ModelSelector.SelectedItem
        if selected:
            self.model = selected
            self.refresh_model_info()

    def refresh_model_info(self):
        if not ollama_is_installed():
            self.ModelInfo.Text = "Ollama not found. Please install Ollama."
            return

        if not ollama_model_installed(self.model):
            self.ModelInfo.Text = "Model '{}' not installed.".format(self.model)
        else:
            self.ModelInfo.Text = "Model: {} (active)".format(self.model)

    # === Ollama Chat tab logic ---
    def on_send_chat(self, sender, args):
        import System
        import time

        prompt = self.ChatInput.Text.strip()
        if not prompt:
            return

        self._set_thinking("Thinking (Chat)...")
        self.show_busy()
        self._pump_ui()

        try:
            self.ChatHistory.AppendText("You: {}\n".format(prompt))
            # Simulate long call
            # time.sleep(5)  # For demo, remove in production
            reply = send_ollama_chat(self.model, prompt)
            self.ChatHistory.AppendText("AI: {}\n\n".format(reply))
            self.ChatInput.Text = ""
        except Exception as e:
            self.ChatHistory.AppendText("Error: {}\n".format(str(e)))
        finally:
            self.hide_busy()
            self._set_thinking("Thinking...")

    # --- ModelMind tab logic ---
    def on_modelmind_send(self, sender, args):
        prompt = self.ModelMindInput.Text.strip()
        if not prompt:
            return

        self._set_thinking("Thinking (ModelMind)...")
        self.show_busy()
        self._pump_ui()

        try:
            self.ModelMindHistory.AppendText("You: {}\n".format(prompt))
            # ... rest of your code
            # (AI call, extract, etc)

            # Try public commands first
            public_cmd_result = handle_public_command(prompt, doc, uidoc)
            if public_cmd_result:
                self.ModelMindHistory.AppendText(
                    "Result: {}\n\n".format(public_cmd_result)
                )
                self.pending_ai_code = None  # clear pending code
                self.ApproveCodeButton.IsEnabled = False
                return

            # No match: Try AI codegen
            code_prompt = (
                "You are an expert Revit Python (IronPython) assistant. "
                "Given the following task, output ONLY a working Python script for Revit using the Revit API. "
                "Wrap your answer in triple backticks with 'python'. "
                "Assume 'doc' is the current Document, 'uidoc' is the ActiveUIDocument, and 'DB' is imported. "
                "Do not explain, only give code. "
                "Task: {}".format(prompt)
            )
            ai_reply = send_ollama_chat(self.model, code_prompt)
            self.ModelMindHistory.AppendText(
                "AI-generated code (review before running):\n{}\n".format(ai_reply)
            )
            # Try to extract code block for approval
            code_blocks = extract_python_code(ai_reply)
            if code_blocks and len(code_blocks[0].strip()) > 0:
                self.pending_ai_code = code_blocks[0]
                self.ApproveCodeButton.IsEnabled = True
                self.ModelMindHistory.AppendText(
                    "Click 'Approve & Run Code' to execute.\n"
                )
            else:
                self.pending_ai_code = None
                self.ApproveCodeButton.IsEnabled = False
                self.ModelMindHistory.AppendText(
                    "No code block detected in AI reply.\n"
                )

        except Exception as e:
            self.ModelMindHistory.AppendText("Error: {}\n".format(str(e)))
        finally:
            self.hide_busy()
            self._set_thinking("Thinking...")

    def on_approve_code(self, sender, args):
        if not self.pending_ai_code or len(self.pending_ai_code.strip()) == 0:
            self.ModelMindHistory.AppendText("No code to run.\n")
            return
        self._set_thinking("Running code...")
        self.show_busy()
        self._pump_ui()
        try:
            sanitized_code = sanitize_llm_code(self.pending_ai_code)
            self.ModelMindHistory.AppendText(
                "Running AI code:\n{}\n".format(sanitized_code)
            )
            result = run_code_in_revit(sanitized_code, doc, uidoc)
            self.ModelMindHistory.AppendText("AI code result: {}\n".format(result))
        except Exception as e:
            self.ModelMindHistory.AppendText("AI code error: {}\n".format(str(e)))
        finally:
            self.pending_ai_code = None
            self.ApproveCodeButton.IsEnabled = False
            self.hide_busy()
            self._set_thinking("Thinking...")

    def on_upgrade_model(self, sender, args):
        self.ModelInfo.Text = "Upgrading model: {} ...".format(self.model)
        if pull_ollama_model(self.model):
            self.ModelInfo.Text = "Model {} upgraded.".format(self.model)
        else:
            self.ModelInfo.Text = "Failed to upgrade model: {}".format(self.model)

    def _on_header_drag(self, sender, e):
        import System.Windows.Input as wpfInput

        src = e.OriginalSource
        try:
            tname = src.GetType().Name if hasattr(src, "GetType") else ""
        except:
            tname = ""
        if tname in (
            "Button",
            "TextBox",
            "ComboBox",
            "ListBox",
            "ListBoxItem",
            "RichTextBox",
        ):
            return

        if e.LeftButton == wpfInput.MouseButtonState.Pressed:
            try:
                self.DragMove()
                e.Handled = True
            except:
                pass

    def _pump_ui(self):
        self.Dispatcher.Invoke(
            System.Windows.Threading.DispatcherPriority.Background, Action(do_nothing)
        )

    def on_close(self, sender, args):
        self.Close()


# print("About to run main() in", __file__)
# === Script Entry Point ===


def main():
    # 1. Check Ollama presence
    if not ollama_is_installed():
        forms.alert(
            "Ollama is not installed. Please install Ollama first:\nhttps://ollama.com/download",
            exitscript=True,
        )

    # 2. Check if model installed, if not, offer to pull
    if not ollama_model_installed(DEFAULT_MODEL):
        if not pull_ollama_model(DEFAULT_MODEL):
            forms.alert(
                "Unable to install {}. Exiting.".format(DEFAULT_MODEL), exitscript=True
            )

    # 3. Show chat UI
    win = OllamaAIChat(XAML_PATH)
    win.ShowDialog()


if __name__ == "__main__":
    main()
