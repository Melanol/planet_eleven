unit = Vulture(center_x=self.our_base.center_x + POS_SPACE,
               center_y=self.our_base.center_y + POS_SPACE)
self.unit_list.append(unit)
unit.move(self.our_base.rally_point_x, self.our_base.rally_point_y)