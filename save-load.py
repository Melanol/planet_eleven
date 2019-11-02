def save(self):
    savefile = open("save.p", "wb")
    pickle.dump(left_view_border, savefile)
    pickle.dump(bottom_view_border, savefile)
    pickle.dump(self.frame_count, savefile)
    pickle.dump(self.npa, savefile)

    pickle.dump(self.minimap_textured_background.x, savefile)
    pickle.dump(self.minimap_textured_background.y, savefile)
    pickle.dump(self.control_panel_sprite.x, savefile)
    pickle.dump(self.control_panel_sprite.y, savefile)
    pickle.dump(self.control_panel_buttons_background.x, savefile)
    pickle.dump(self.control_panel_buttons_background.y, savefile)
    pickle.dump(self.move_button.x, savefile)
    pickle.dump(self.move_button.y, savefile)
    pickle.dump(self.stop_button.x, savefile)
    pickle.dump(self.stop_button.y, savefile)
    pickle.dump(self.attack_button.x, savefile)
    pickle.dump(self.attack_button.y, savefile)
    pickle.dump(self.base_button.x, savefile)
    pickle.dump(self.base_button.y, savefile)
    pickle.dump(self.defiler_button.x, savefile)
    pickle.dump(self.defiler_button.y, savefile)
    pickle.dump(self.centurion_button.x, savefile)
    pickle.dump(self.centurion_button.y, savefile)
    pickle.dump(self.vulture_button.x, savefile)
    pickle.dump(self.vulture_button.y, savefile)
    pickle.dump(self.pioneer_button.x, savefile)
    pickle.dump(self.pioneer_button.y, savefile)
    pickle.dump(minimap_fow_x, savefile)
    pickle.dump(minimap_fow_y, savefile)
    pickle.dump(self.minimap_cam_frame_sprite.x, savefile)
    pickle.dump(self.minimap_cam_frame_sprite.y, savefile)

    pickle.dump(len(our_buildings_list), savefile)
    for building in our_buildings_list:
        pickle.dump(str(type(building)), savefile)
        pickle.dump(building.x, savefile)
        pickle.dump(building.y, savefile)
        pickle.dump(building.hp, savefile)
        pickle.dump(building.rally_point_x, savefile)
        pickle.dump(building.rally_point_y, savefile)
        pickle.dump(building.building_queue, savefile)
        pickle.dump(building.current_building_time, savefile)
        pickle.dump(building.building_complete, savefile)
        pickle.dump(building.building_start_time, savefile)

    pickle.dump(len(our_units_list), savefile)
    for unit in our_units_list:
        pickle.dump(str(type(unit)), savefile)
        pickle.dump(unit.x, savefile)
        pickle.dump(unit.y, savefile)
        pickle.dump(unit.rotation, savefile)
        pickle.dump(unit.hp, savefile)
        pickle.dump(unit.destination_reached, savefile)
        pickle.dump(unit.movement_interrupted, savefile)
        pickle.dump(unit.target_x, savefile)
        pickle.dump(unit.target_y, savefile)
        pickle.dump(unit.destination_x, savefile)
        pickle.dump(unit.destination_y, savefile)
        pickle.dump(unit.velocity_x, savefile)
        pickle.dump(unit.velocity_y, savefile)
        pickle.dump(unit.on_cooldown, savefile)
        pickle.dump(unit.cooldown_started, savefile)

    pickle.dump(len(enemy_buildings_list), savefile)
    for building in enemy_buildings_list:
        pickle.dump(str(type(building)), savefile)
        pickle.dump(building.x, savefile)
        pickle.dump(building.y, savefile)
        pickle.dump(building.hp, savefile)
        pickle.dump(building.rally_point_x, savefile)
        pickle.dump(building.rally_point_y, savefile)
        pickle.dump(building.building_queue, savefile)
        pickle.dump(building.current_building_time, savefile)
        pickle.dump(building.building_complete, savefile)
        pickle.dump(building.building_start_time, savefile)

    pickle.dump(len(projectile_list), savefile)
    for projectile in projectile_list:
        pickle.dump(projectile.x, savefile)
        pickle.dump(projectile.y, savefile)
        pickle.dump(projectile.damage, savefile)
        pickle.dump(projectile.speed, savefile)
        pickle.dump(projectile.target_x, savefile)
        pickle.dump(projectile.target_y, savefile)
        pickle.dump(projectile.rotation, savefile)
        pickle.dump(projectile.velocity_x, savefile)
        pickle.dump(projectile.velocity_y, savefile)

    # print('saved')


def load(self):
    global left_view_border, bottom_view_border, minimap_fow_x, minimap_fow_y
    self.clear_level()
    savefile = open("save.p", "rb")
    left_view_border = pickle.load(savefile)
    bottom_view_border = pickle.load(savefile)
    self.frame_count = pickle.load(savefile)
    self.npa = pickle.load(savefile)
    self.minimap_fow_ImageData.set_data('RGBA', self.minimap_fow_ImageData.width * 4,
                                        data=self.npa.tobytes())

    self.minimap_textured_background.x = pickle.load(savefile)
    self.minimap_textured_background.y = pickle.load(savefile)
    self.control_panel_sprite.x = pickle.load(savefile)
    self.control_panel_sprite.y = pickle.load(savefile)
    self.control_panel_buttons_background.x = pickle.load(savefile)
    self.control_panel_buttons_background.y = pickle.load(savefile)
    self.move_button.x = pickle.load(savefile)
    self.move_button.y = pickle.load(savefile)
    self.stop_button.x = pickle.load(savefile)
    self.stop_button.y = pickle.load(savefile)
    self.attack_button.x = pickle.load(savefile)
    self.attack_button.y = pickle.load(savefile)
    self.base_button.x = pickle.load(savefile)
    self.base_button.y = pickle.load(savefile)
    self.defiler_button.x = pickle.load(savefile)
    self.defiler_button.y = pickle.load(savefile)
    self.centurion_button.x = pickle.load(savefile)
    self.centurion_button.y = pickle.load(savefile)
    self.vulture_button.x = pickle.load(savefile)
    self.vulture_button.y = pickle.load(savefile)
    self.pioneer_button.x = pickle.load(savefile)
    self.pioneer_button.y = pickle.load(savefile)
    minimap_fow_x = pickle.load(savefile)
    minimap_fow_y = pickle.load(savefile)
    self.minimap_cam_frame_sprite.x = pickle.load(savefile)
    self.minimap_cam_frame_sprite.y = pickle.load(savefile)

    our_buildings_list_len = pickle.load(savefile)
    for _ in range(our_buildings_list_len):
        building_type = pickle.load(savefile)
        x = pickle.load(savefile)
        y = pickle.load(savefile)

    our_units_list_len = pickle.load(savefile)
    for _ in range(our_units_list_len):
        unit_type = pickle.load(savefile)
        x = pickle.load(savefile)
        y = pickle.load(savefile)
        rotation = pickle.load(savefile)
        if unit_type == "<class '__main__.Defiler'>":
            unit = Defiler(self, x=x, y=y)
        elif unit_type == "<class '__main__.Centurion'>":
            unit = Centurion(self, x=x, y=y)
        elif unit_type == "<class '__main__.Vulture'>":
            unit = Vulture(self, x=x, y=y)
        elif unit_type == "<class '__main__.Pioneer'>":
            unit = Pioneer(self, x=x, y=y)
        unit.spawn()
        unit.rotation = rotation
        unit.hp = pickle.load(savefile)
        unit.destination_reached = pickle.load(savefile)
        unit.movement_interrupted = pickle.load(savefile)
        unit.target_x = pickle.load(savefile)
        unit.target_y = pickle.load(savefile)
        unit.destination_x = pickle.load(savefile)
        unit.destination_y = pickle.load(savefile)
        unit.velocity_x = pickle.load(savefile)
        unit.velocity_y = pickle.load(savefile)
        unit.on_cooldown = pickle.load(savefile)
        unit.cooldown_started = pickle.load(savefile)
        unit.shadow.rotation = unit.rotation
        unit.shadow.velocity_x = unit.velocity_x
        unit.shadow.velocity_y = unit.velocity_y

    enemy_buildings_list_len = pickle.load(savefile)
    for _ in range(enemy_buildings_list_len):
        building_type = pickle.load(savefile)
        x = pickle.load(savefile)
        y = pickle.load(savefile)

    projectile_list_len = pickle.load(savefile)
    for _ in range(projectile_list_len):
        x = pickle.load(savefile)
        y = pickle.load(savefile)
        damage = pickle.load(savefile)
        speed = pickle.load(savefile)
        target_x = pickle.load(savefile)
        target_y = pickle.load(savefile)
        rotation = pickle.load(savefile)
        velocity_x = pickle.load(savefile)
        velocity_y = pickle.load(savefile)
        projectile = Projectile(x, y, target_x, target_y, damage, speed, None)
        projectile_list.append(projectile)
        projectile.rotation = rotation
        projectile.velocity_x = velocity_x
        projectile.velocity_y = velocity_y
        # print('target_x =', target_x)
        # print('target_y =', target_y)
        for building in enemy_buildings_list:
            # print('building.x =', building.x)
            # print('building.y =', building.y)
            if building.x == target_x and building.y == target_y:
                projectile.target_obj = building
                break
        # print(projectile.target_obj)

    # print('loaded')