from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
from database import get_characters, get_episodes, get_relations, get_staff, get_work, set_episode_watched
from ui.theme import COLORS, muted_label_stylesheet
from ui.widgets.character_card import CharacterCard
from ui.widgets.person_card import PersonCard
from ui.widgets.relation_card import RelationCard


class WorkDetailPage(QWidget):
    back_requested=Signal(); person_selected=Signal(object); character_selected=Signal(object); relation_selected=Signal(object)
    def __init__(self):
        super().__init__(); self.work=None; self.scroll_area=QScrollArea(); self.scroll_area.setWidgetResizable(True); self.scroll_area.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding); root=QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.addWidget(self.scroll_area)

    def set_work(self,work):
        self.work=work; content=QWidget(); root=QVBoxLayout(content); root.setContentsMargins(42,34,42,50); root.setSpacing(22)
        back=QPushButton("‹  Back to Library"); back.setObjectName("back"); back.clicked.connect(self.back_requested); root.addWidget(back,alignment=Qt.AlignLeft)
        root.addWidget(self._hero()); root.addWidget(self._description()); root.addWidget(self._episodes_section()); root.addWidget(self._grid_section("Characters",get_characters(self._value("id")),CharacterCard,self.character_selected,4)); root.addWidget(self._grid_section("Staff",get_staff(self._value("id")),PersonCard,self.person_selected,4)); root.addWidget(self._relations()); root.addStretch(); self.scroll_area.setWidget(content)
        self.setStyleSheet(f"""
            QPushButton#back {{ background:transparent; border:0; color:{COLORS['secondary']}; padding:5px 0; font-weight:750; }}
            QFrame#hero {{ background:{COLORS['surface']}; border:1px solid {COLORS['border']}; border-radius:22px; }}
            QFrame#section {{ background:{COLORS['surface']}; border:1px solid {COLORS['border']}; border-radius:18px; }}
            QFrame#episode {{ background:{COLORS['surface_alt']}; border:1px solid {COLORS['border']}; border-radius:10px; }}
            QFrame#episode:hover {{ border-color:{COLORS['border_hover']}; }}
            QCheckBox::indicator {{ width:18px; height:18px; border-radius:5px; border:1px solid {COLORS['border_hover']}; background:{COLORS['background_alt']}; }}
            QCheckBox::indicator:checked {{ background:{COLORS['accent']}; border-color:{COLORS['accent']}; }}
        """)

    def _hero(self):
        hero=QFrame(); hero.setObjectName("hero"); box=QHBoxLayout(hero); box.setContentsMargins(24,24,28,24); box.setSpacing(30)
        cover=QLabel(); cover.setFixedSize(235,335); cover.setAlignment(Qt.AlignCenter); path=self._value("cover_path")
        if path:
            pix=QPixmap(str(path))
            if not pix.isNull(): cover.setPixmap(pix.scaled(235,335,Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation))
        if cover.pixmap() is None or cover.pixmap().isNull(): cover.setText("NO COVER"); cover.setStyleSheet(f"color:{COLORS['muted']};background:{COLORS['background_alt']};border-radius:14px;")
        box.addWidget(cover,alignment=Qt.AlignTop)
        info=QVBoxLayout(); info.setSpacing(9)
        t=QLabel(self._title()); t.setWordWrap(True); t.setStyleSheet(f"font-size:34px;font-weight:850;color:{COLORS['primary']};letter-spacing:-1px;"); info.addWidget(t)
        alt=self._value("native") or self._value("title_native") or ""
        if alt: a=QLabel(str(alt)); a.setStyleSheet(muted_label_stylesheet()); info.addWidget(a)
        meta="  ·  ".join(str(x) for x in [self._value("format"),self._value("start_year"),f"{self._value('episodes')} eps" if self._value('episodes') else None,f"{self._value('chapters')} ch" if self._value('chapters') else None] if x)
        if meta: m=QLabel(meta); m.setStyleSheet(f"color:{COLORS['secondary']};font-size:13px;"); info.addWidget(m)
        score=self._value("score") or self._value("averageScore"); s=QLabel(f"★  {score}%" if score else "—  No score"); s.setStyleSheet(f"color:{COLORS['accent']};font-size:18px;font-weight:800;"); info.addWidget(s)
        info.addStretch(); box.addLayout(info,1); return hero

    def _description(self):
        frame=QFrame(); frame.setObjectName("section"); lay=QVBoxLayout(frame); lay.setContentsMargins(20,18,20,20); lay.setSpacing(10); h=QLabel("Overview"); h.setStyleSheet(f"font-size:17px;font-weight:800;color:{COLORS['primary']};"); lay.addWidget(h); label=QLabel(self._value("description") or "No description saved locally."); label.setWordWrap(True); label.setTextFormat(Qt.PlainText); label.setStyleSheet(f"color:{COLORS['secondary']};font-size:14px;"); lay.addWidget(label); return frame

    def _episodes_section(self):
        episodes=get_episodes(self._value("id")); frame=QFrame(); frame.setObjectName("section"); lay=QVBoxLayout(frame); lay.setContentsMargins(20,18,20,20); lay.setSpacing(10)
        header=QHBoxLayout(); title=QLabel("Episodes"); title.setStyleSheet(f"font-size:17px;font-weight:800;color:{COLORS['primary']};"); header.addWidget(title); header.addStretch()
        watched=sum(1 for ep in episodes if ep['watched']); total=len(episodes); count=QLabel(f"{watched} / {total} watched" if total else "No episodes saved"); count.setStyleSheet(f"color:{COLORS['accent']};font-weight:800;"); header.addWidget(count); lay.addLayout(header)
        if not episodes:
            x=QLabel("Episode data will appear here when it has been saved locally."); x.setStyleSheet(muted_label_stylesheet()); lay.addWidget(x); return frame
        for ep in episodes:
            row=QFrame(); row.setObjectName("episode"); r=QHBoxLayout(row); r.setContentsMargins(12,9,14,9); cb=QCheckBox(); cb.setChecked(bool(ep['watched'])); r.addWidget(cb)
            num=QLabel(f"EP {ep['episode_number']:02d}"); num.setMinimumWidth(52); num.setStyleSheet(f"color:{COLORS['accent']};font-weight:850;"); r.addWidget(num)
            title=QLabel(ep['title'] or "Episode"); title.setStyleSheet(f"color:{COLORS['primary']};font-weight:650;"); r.addWidget(title,1)
            date=QLabel(str(ep['air_date'] or "")); date.setStyleSheet(muted_label_stylesheet()); r.addWidget(date); cb.toggled.connect(lambda checked,n=ep['episode_number']:self._episode_toggled(n,checked)); lay.addWidget(row)
        return frame

    def _episode_toggled(self,n,checked): set_episode_watched(self._value("id"),n,checked); refreshed=get_work(self._value("id")); self.set_work(refreshed or self.work)

    def _grid_section(self,title,items,cls,signal,columns):
        frame=QFrame(); frame.setObjectName("section"); lay=QVBoxLayout(frame); lay.setContentsMargins(20,18,20,20); lay.setSpacing(12); h=QLabel(title); h.setStyleSheet(f"font-size:17px;font-weight:800;color:{COLORS['primary']};"); lay.addWidget(h); container=QWidget(); grid=QGridLayout(container); grid.setContentsMargins(0,0,0,0); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(12)
        if not items: x=QLabel("Nothing stored locally yet."); x.setStyleSheet(muted_label_stylesheet()); grid.addWidget(x,0,0)
        else:
            for i,item in enumerate(items): card=cls(item); card.clicked.connect(signal); grid.addWidget(card,i//columns,i%columns)
        lay.addWidget(container); return frame

    def _relations(self): return self._grid_section("Relations",get_relations(self._value("id")),RelationCard,self.relation_selected,2)
    def _value(self,key):
        if hasattr(self.work,'get'): return self.work.get(key)
        try:return self.work[key]
        except (KeyError,IndexError,TypeError):return None
    def _title(self):
        t=self._value('title'); return (t.get('english') or t.get('romaji') or t.get('native') or 'Untitled') if isinstance(t,dict) else (t or 'Untitled')
