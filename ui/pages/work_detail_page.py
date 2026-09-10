from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
from database import get_characters, get_episodes, get_relations, get_staff, get_work, set_episode_watched
from ui.theme import COLORS, SPACING, muted_label_stylesheet
from ui.widgets.character_card import CharacterCard
from ui.widgets.person_card import PersonCard
from ui.widgets.relation_card import RelationCard
from ui.widgets.progress_bar import ProgressBar


class WorkDetailPage(QWidget):
    back_requested=Signal(); person_selected=Signal(object); character_selected=Signal(object); relation_selected=Signal(object)
    def __init__(self):
        super().__init__(); self.work=None; self.scroll_area=QScrollArea(); self.scroll_area.setWidgetResizable(True); self.scroll_area.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding); root=QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.addWidget(self.scroll_area)

    def set_work(self,work):
        self.work=work; content=QWidget(); root=QVBoxLayout(content); root.setContentsMargins(42,34,42,50); root.setSpacing(20)
        back=QPushButton("‹  Library"); back.setObjectName("back"); back.clicked.connect(self.back_requested); root.addWidget(back,alignment=Qt.AlignLeft)
        root.addWidget(self._hero()); root.addWidget(self._section("Description",self._description())); root.addWidget(self._episodes_section()); root.addWidget(self._grid_section("Characters",get_characters(self._value("id")),CharacterCard,self.character_selected,3)); root.addWidget(self._grid_section("Staff",get_staff(self._value("id")),PersonCard,self.person_selected,4)); root.addWidget(self._relations()); root.addStretch(); self.scroll_area.setWidget(content)
        self.setStyleSheet(f"QPushButton#back{{background:transparent;border:0;color:{COLORS['secondary']};padding:5px 0;font-weight:700;}} QFrame#hero{{background:{COLORS['surface']};border:1px solid {COLORS['border']};border-radius:22px;}} QFrame#stat{{background:{COLORS['surface_alt']};border:1px solid {COLORS['border']};border-radius:12px;}}")

    def _hero(self):
        hero=QFrame(); hero.setObjectName("hero"); box=QHBoxLayout(hero); box.setContentsMargins(24,24,28,24); box.setSpacing(28)
        cover=QLabel(); cover.setFixedSize(235,335); cover.setAlignment(Qt.AlignCenter); path=self._value("cover_path")
        if path:
            pix=QPixmap(str(path));
            if not pix.isNull(): cover.setPixmap(pix.scaled(235,335,Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation))
        if not cover.pixmap(): cover.setText("NO COVER"); cover.setStyleSheet(f"color:{COLORS['muted']};background:{COLORS['background_alt']};border-radius:14px;")
        box.addWidget(cover,alignment=Qt.AlignTop); info=QVBoxLayout(); info.setSpacing(10)
        title=self._title(); t=QLabel(title); t.setWordWrap(True); t.setStyleSheet(f"font-size:34px;font-weight:850;color:{COLORS['primary']};letter-spacing:-1px;"); info.addWidget(t)
        alt=self._value("native") or self._value("title_native") or ""; 
        if alt: a=QLabel(str(alt)); a.setStyleSheet(muted_label_stylesheet()); info.addWidget(a)
        meta="  ·  ".join(str(x) for x in [self._value("format"),self._value("start_year"),f"{self._value('episodes')} eps" if self._value('episodes') else None,f"{self._value('chapters')} ch" if self._value('chapters') else None] if x)
        m=QLabel(meta); m.setStyleSheet(f"color:{COLORS['secondary']};font-size:13px;"); info.addWidget(m)
        score=self._value("score"); s=QLabel(f"★  {score}%" if score else "—  No score"); s.setStyleSheet(f"color:{COLORS['accent']};font-size:18px;font-weight:800;"); info.addWidget(s)
        info.addSpacing(12); p=self._value("progress_episodes") or 0; total=self._value("episodes") or 0; pl=QLabel(f"Progress   {p} / {total}" if total else f"Progress   {p}"); pl.setStyleSheet(f"color:{COLORS['secondary']};font-weight:700;"); info.addWidget(pl); info.addWidget(ProgressBar(p,total)); info.addStretch(); box.addLayout(info,1); return hero

    def _description(self):
        label=QLabel(self._value("description") or "No description saved locally."); label.setWordWrap(True); label.setTextFormat(Qt.PlainText); label.setStyleSheet(f"color:{COLORS['secondary']};font-size:14px;line-height:1.5;"); return label

    def _section(self,title,widget):
        frame=QFrame(); frame.setObjectName("section"); lay=QVBoxLayout(frame); lay.setContentsMargins(20,18,20,20); lay.setSpacing(12); h=QLabel(title); h.setStyleSheet(f"font-size:17px;font-weight:800;color:{COLORS['primary']};"); lay.addWidget(h); lay.addWidget(widget); return frame

    def _episodes_section(self):
        episodes=get_episodes(self._value("id")); container=QWidget(); lay=QVBoxLayout(container); lay.setContentsMargins(0,0,0,0); lay.setSpacing(7)
        if not episodes:
            x=QLabel("No episode data stored locally."); x.setStyleSheet(muted_label_stylesheet()); lay.addWidget(x); return self._section("Episodes",container)
        for ep in episodes:
            row=QFrame(); row.setObjectName("episode"); r=QHBoxLayout(row); r.setContentsMargins(12,8,12,8); cb=QCheckBox(); cb.setChecked(bool(ep['watched'])); num=QLabel(f"{ep['episode_number']:02d}"); num.setStyleSheet(f"color:{COLORS['accent']};font-weight:800;min-width:28px;"); r.addWidget(cb); r.addWidget(num); title=QLabel(ep['title'] or "Episode"); title.setStyleSheet(f"color:{COLORS['primary']};font-weight:600;"); r.addWidget(title,1); date=QLabel(str(ep['air_date'] or "")); date.setStyleSheet(muted_label_stylesheet()); r.addWidget(date); cb.toggled.connect(lambda checked,n=ep['episode_number']:self._episode_toggled(n,checked)); lay.addWidget(row)
        return self._section("Episodes",container)

    def _episode_toggled(self,n,checked): set_episode_watched(self._value("id"),n,checked); refreshed=get_work(self._value("id")); self.set_work(refreshed or self.work)

    def _grid_section(self,title,items,cls,signal,columns):
        container=QWidget(); grid=QGridLayout(container); grid.setContentsMargins(0,0,0,0); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(12)
        if not items:
            x=QLabel("Nothing stored locally yet."); x.setStyleSheet(muted_label_stylesheet()); grid.addWidget(x,0,0); return self._section(title,container)
        for i,item in enumerate(items):
            card=cls(item); card.clicked.connect(signal); grid.addWidget(card,i//columns,i%columns)
        return self._section(title,container)

    def _relations(self):
        return self._grid_section("Relations",get_relations(self._value("id")),RelationCard,self.relation_selected,2)

    def _value(self,key):
        if hasattr(self.work,'get'): return self.work.get(key)
        try:return self.work[key]
        except (KeyError,IndexError,TypeError):return None
    def _title(self):
        t=self._value('title'); return (t.get('english') or t.get('romaji') or t.get('native') or 'Untitled') if isinstance(t,dict) else (t or 'Untitled')
