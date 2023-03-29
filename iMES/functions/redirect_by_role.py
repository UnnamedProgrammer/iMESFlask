from flask import redirect, render_template

def redirect_by_role(role_list: dict, current_tpa):
    '''Функция редиректит пользователя согласно его роли'''
    # Если есть сохранённая роль то редиректим в интерфейс согласно роли
    if role_list['SavedRoles'] != None:
        if (role_list['SavedRoles'] == 'Оператор'):
            return redirect('/operator')
        elif (role_list['SavedRoles'] == 'Наладчик'):
            return redirect('/adjuster')

    # Если у пользователя одна роль то редиректим в интерфейс согласно роли
    if len(role_list['Roles']) == 1:
        if (role_list['Roles'][0] == 'Оператор'):
            return redirect('/operator')
        elif (role_list['Roles'][0] == 'Наладчик'):
            return redirect('/adjuster')
    # Если несколько то редиректим в меню для выбора интерфейса
    elif len(role_list['Roles']) > 1:
        return redirect('/menu')
    # Иначе выдаём ошибку
    else:
        error = "У вас нет ни одной роли, обратитесь к администратору системы"
        return render_template('Show_error.html', error=error, ret='/',current_tpa=current_tpa)