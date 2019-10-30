# The origin of the angle here is the destination point
            diff_x = self.x - self.destination_x
            diff_y = self.y - self.destination_y
            angle = math.atan2(diff_y, diff_x)  # Rad
            d_angle = math.degrees(angle)
            rounded_d_angle = 45 * round(d_angle / 45)
            if rounded_d_angle <= 0:
                rounded_d_angle += 360
            if rounded_d_angle == 360:
                dx, dy = POS_SPACE, 0
            elif rounded_d_angle == 45:
                dx, dy = POS_SPACE, POS_SPACE
            elif rounded_d_angle == 90:
                dx, dy = 0, POS_SPACE
            elif rounded_d_angle == 135:
                dx, dy = -POS_SPACE, POS_SPACE
            elif rounded_d_angle == 180:
                dx, dy = -POS_SPACE, 0
            elif rounded_d_angle == 225:
                dx, dy = -POS_SPACE, -POS_SPACE
            elif rounded_d_angle == 270:
                dx, dy = 0, -POS_SPACE
            elif rounded_d_angle == 315:
                dx, dy = POS_SPACE, -POS_SPACE
            print('rounded_d_angle =', rounded_d_angle)
            print('dx =', dx, 'dy =', dy)

            while True:
                if selected_dict[(self.destination_x, self.destination_y)] is None:
                    break
                self.destination_x += dx
                self.destination_y += dy
                if self.x == self.destination_x and self.y == self.destination_y:
                    self.destination_reached = True
                    return