
class Block(Building):
    def __init__(self, outer_instance, our_img, enemy_img, x, y, hp, is_enemy, vision_radius=3):
        super().__init__(outer_instance, our_img, enemy_img, x, y, hp, is_enemy, vision_radius)


class ClusteredBuilding:
    def __init__(self, outer_instance, our_img, enemy_img, x, y, width, hp, is_enemy, vision_radius=4):
        self.x = x
        self.y = y
        self.outer_instance = outer_instance
        self.hp = hp
        ground_pos_coords_dict[(x, y)] = self
        self.default_rally_point = True
        self.is_enemy = is_enemy
        if not self.is_enemy:
            our_buildings_list.append(self)
            img = our_img
            minimap_pixel = res.minimap_our_image
            outer_instance.update_fow(x=x, y=y, radius=vision_radius)
        else:
            enemy_buildings_list.append(self)
            img = enemy_img
            minimap_pixel = res.minimap_enemy_image
        pixel_minimap_coords = to_minimap(self.x, self.y)
        self.pixels = []
        self.pixels.append(pyglet.sprite.Sprite(img=minimap_pixel, x=pixel_minimap_coords[0],
                                                y=pixel_minimap_coords[1],
                                                batch=minimap_pixels_batch))
        self.blocks = []

    def grow(self):
        current_width = 1
        x = self.x
        y = self.y
        # Go right
        for n in range(current_width + 1):
            block = Block(x, y)
            self.blocks.append(block)
        # Go up
        for n in range(current_width):
            pass
        # Go left
        for n in range(current_width):
            pass
        # Go down
        for n in range(current_width):
            pass



    def kill(self, delay_del=False):
        global ground_pos_coords_dict, our_buildings_list, enemy_buildings_list
        ground_pos_coords_dict[(self.x, self.y)] = None
        for pixel in self.pixels:
            pixel.delete()
        if not delay_del:
            if not self.is_enemy:
                del our_buildings_list[our_buildings_list.index(self)]
            else:
                del enemy_buildings_list[enemy_buildings_list.index(self)]
        for block in self.blocks:
            self.delete()