import tempfile
import shutil
from pathlib import Path
from devforge.core.custom_generator import create_structure

def test_create_structure_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)

        structure_text = """sellwrite-ai/
├── backend/
│   ├── routes/
│   └── models/
└── frontend/
    └── src/
"""

        project_root = create_structure(str(base_path), structure_text)
        root_dir = base_path / "sellwrite-ai"

        assert root_dir.exists() and root_dir.is_dir()

        assert (root_dir / "backend").exists()
        assert (root_dir / "backend" / "routes").exists()
        assert (root_dir / "backend" / "models").exists()
        assert (root_dir / "frontend" / "src").exists()
