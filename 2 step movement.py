'''@staticmethod
    def set_path(x, y, target_x, target_y):
        diff_x = target_x - x
        diff_y = target_y - y
        print('x = {}\ny = {}\ntarget_x = {}\ntarget_y = {}'.format(x, y, target_x, target_y))
        print('diff_x = {}\ndiff_y = {}'.format(diff_x, diff_y))
        # Pathfinding
        path = []
        angle = math.atan2(diff_y, diff_x)  # Rad
        angle = math.degrees(angle)
        angle = round_angle(angle)
        print('angle =', angle)
        next_target = check_if_move_possible(x, y, angle)[1]
        if next_target:
            path.append(next_target)

        # Pathing (2 steps):
        if diff_x == 0 or diff_y == 0 or abs(diff_x) == abs(diff_y):
            print('case 1: straight line', 'target_x =', target_x, 'target_y =', target_y)
            return [(target_x, target_y)]
        else:
            if abs(diff_x) < abs(diff_y):
                print('case 2: abs(diff_x) < abs(diff_y)')
                if diff_y > 0:
                    return [(target_x, y + abs(diff_x)), (target_x, target_y)]
                else:
                    return [(target_x, y - abs(diff_x)), (target_x, target_y)]
            else:
                print('case 3: abs(diff_x) > abs(diff_y)')
                if diff_x > 0:
                    return [(x + abs(diff_y), target_y), (target_x, target_y)]
                else:
                    return [(x - abs(diff_y), target_y), (target_x, target_y)]'''