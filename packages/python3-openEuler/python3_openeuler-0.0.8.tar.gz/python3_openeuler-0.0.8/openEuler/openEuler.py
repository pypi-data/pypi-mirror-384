import re
import logging
import tempfile
from pathlib import Path
from pyrpm.spec import Spec
import git
import requests
from bs4 import BeautifulSoup
import traceback
import functools
import inspect
from typing import Callable, Any
from typing import List, Dict, Any, Optional

import requests.exceptions
from typing import Generator, Optional,Tuple

log=logging.getLogger(__name__)

def enter_and_leave_function(func: Callable) -> Callable:
    """
    函数调用日志装饰器：
    1. 记录函数入参、调用位置
    2. 正常执行时记录返回值
    3. 异常时记录完整堆栈（含函数内具体报错行数）
    """

    @functools.wraps(func)  # 保留原函数元信息（如 __name__、__doc__）
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 获取函数定义的文件路径和行号（基础位置信息）
        func_def_file = inspect.getsourcefile(func) or "unknown_file"
        func_def_file = func_def_file.split("/")[-1]
        func_def_line = inspect.getsourcelines(func)[1] if func_def_file != "unknown_file" else "unknown_line"
        log.info(
            f"[{func_def_file}: {func_def_line}]"
            f"[{func.__name__}()]"
            f"| args={args}, kwargs={kwargs}"
        )

        try:
            result = func(*args, **kwargs)
            log.info(
                f"[{func_def_file}: {func_def_line}]"
                f" finish run function {func.__name__}(), return value is: {result} "
            )
            return result

        except Exception as e:
            error_traceback = traceback.format_exc()

            log.error(
                f"[{func_def_file}: {func_def_line}]"
                f"failed to run function {func.__name__}() :Failed. "
                f"| error_type：{type(e).__name__} "
                f"| error_message：{str(e)} "
                f"| full_stack_trace：\n{error_traceback}",
                exc_info=False  # 已手动捕获堆栈，避免 logging 重复打印
            )
            raise  # 重新抛出异常，不中断原异常链路

    return wrapper

class Gitee():
    def __init__(self):
        self.__base_url= "https://gitee.com/api/v5"
        self.__access_token="aa6cb32539129acf5605793f91a1588c"

    def get_branches_list_by_repo(self,repo_name,owner_name):
        """
        获取仓库的所有分支
        :param repo_name: 仓库名称
        :param owner_name: 仓库所属空间地址(企业、组织或个人的地址
        :return:
        """
        url = f"{self.__base_url}/repos/{owner_name}/{repo_name}/branches"
        page=1
        parameters={
            "access_token":self.__access_token,
            "repo":repo_name,
            "owner":owner_name,
            "sort":"name",
            "direction":"asc",
            "page":page,
            "per_page":10
        }
        headers={
            "Content-Type":"application/json",
            "Accept":"application/json",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
        }
        branches=[]
        while True:
            response=requests.get(url,params=parameters,headers=headers)
            if response.status_code==200:
                data=response.json()
                for branch in data:
                    branches.append(branch["name"])
                page+=1
                parameters["page"]=page
                if len(data)==0:
                    return branches
            else:
                log.error(f"request url is {url}, parameters is {parameters},headers is {headers} failed, response status code is {response.status_code}")
                return branches

    def get_repo_name_and_repo_html_url_by_org(self,org_name):
        log.info(f"begin to get openEuler repo names and repo html urls by org {org_name}...")
        url = f"{self.__base_url}/orgs/{org_name}/repos"
        page=1
        parameters={
            "access_token":"aa6cb32539129acf5605793f91a1588c",
            "org":org_name,
            "page":page,
            "per_page":10,
            "type":"all"
        }
        headers={
            "Content-Type":"application/json",
            "Accept":"application/json",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
        }
        page=1
        log.info(f"begin to request url is {url}, parameters is {parameters},headers is {headers}...")
        while True:
            response=requests.get(url,params=parameters,headers=headers)
            if response.status_code==200:
                data=response.json()
                for repo in data:
                    yield repo["name"],repo["html_url"]
                page+=1
                parameters["page"]=page
                if len(data)==0:
                    break
            else:
                log.error(f"request url is {url}, parameters is {parameters},headers is {headers} failed, response status code is {response.status_code}")
                break


DEFAULT_MACROS = {
    "python3_pkgversion": '3.9',
    "lustre_name":"lustre"
}

class OpenEuler():
    def __init__(self):
        pass

    def __replace_macros(self,value, macros):
        """根据宏字典替换字符串中的宏."""
        if not macros:
            return value

            # 预编译所有宏的正则表达式，提升效率
        patterns = [
            (re.compile(re.escape(key)), val)
            for key, val in macros.items()
        ]

        prev_value = None
        current_value = value
        # 循环替换直到无变化（处理嵌套宏）
        index = 0
        while current_value != prev_value:
            index+=1
            if index>=10:
                break
            prev_value = current_value
            for pattern, replacement in patterns:
                try:
                    current_value = pattern.sub(replacement, current_value)
                except Exception as e:
                    continue
        return current_value


    def __extract_macros(self,spec):
        macros = dict(spec.macros)

        # 补充必要的默认宏（若不存在）
        macros.setdefault("name", spec.name)
        macros.setdefault("version", spec.version)
        macros.setdefault("release", spec.release)

        # 补充全局默认宏（若不存在）
        for key, default_val in DEFAULT_MACROS.items():
            macros.setdefault(key, default_val)

        return macros


    def __get_rpm_list_from_spec(self,spec_file):
        """从 RPM spec 文件中提取所有包名并替换宏。"""
        spec = Spec.from_file(spec_file)
        rpm_list = []
        macros = self.__extract_macros(spec)

        # 提取子包名称
        for pkg in spec.packages:
            subpackage_name = self.__replace_macros(pkg.name, macros)
            if subpackage_name not in rpm_list:
                if "%" in subpackage_name:
                    log.warning(f"{subpackage_name} contains macro, please check")
                else:
                    rpm_list.append(subpackage_name)

        return rpm_list

    def get_openEuler_rpm_names_from_repo(self,os_version,repo_name,repo_url):
        branch=f"openEuler-{os_version}"
        rpm_list = []
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                git.Repo.clone_from(repo_url, temp_dir, branch=branch, depth=1)
                log.info(f"clone {repo_name} success")
            except Exception as e:
                log.error(f"clone {repo_name} failed, error is {e}")
                return rpm_list
            spec_files = list(Path(temp_dir).rglob("*.spec"))

            for spec_file in spec_files:
                temp_list = self.__get_rpm_list_from_spec(spec_file)
                for elem in temp_list:
                    if elem not in rpm_list:
                        rpm_list.append(elem)
        return rpm_list

    def get_openEuler_repo_names_and_urls(
            self,
            os_version: str
    ) -> Generator[Tuple[str, str], None, None]:
        """
        从 Gitee 的 src-openEuler 组织中筛选出包含指定 openEuler 版本分支的仓库信息。

        函数通过调用 Gitee 相关接口，遍历 src-openEuler 组织下的所有仓库，
        检查仓库是否存在与目标 openEuler 版本匹配的分支，若存在则返回该仓库的名称和 HTML 地址。

        Args:
            os_version: 目标 openEuler 版本号（如 "24.03-LTS-SP2"），用于匹配仓库分支

        Yields:
            Generator[Tuple[str, str], None, None]:
                迭代返回符合条件的仓库信息元组：
                - 第一个元素：仓库名称（如 "kernel"）
                - 第二个元素：仓库的 HTML 访问地址（如 "https://gitee.com/src-openEuler/kernel"）

        Notes:
            依赖 Gitee 类的以下方法：
            - get_repo_name_and_repo_html_url_by_org(org_name: str): 用于获取指定组织下所有仓库的名称和 HTML 地址
            - get_branches_list_by_repo(repo_name: str, org_name: str): 用于获取指定仓库的所有分支名称列表
        """
        # 初始化 Gitee 接口操作实例
        log.info("正在初始化 Gitee 接口操作实例...")
        gitee = Gitee()

        # 遍历 src-openEuler 组织下的所有仓库（名称 + HTML 地址）
        for repo_name, repo_url in gitee.get_repo_name_and_repo_html_url_by_org("src-openEuler"):
            log.info(f"正在检查仓库: {repo_name}，地址: {repo_url}")

            # 获取当前仓库的所有分支列表
            branches = gitee.get_branches_list_by_repo(repo_name, "src-openEuler")
            # 处理无分支的异常情况
            if not branches:
                log.warning(f"仓库 {repo_name}（{repo_url}）未发现任何分支，已跳过")
                continue

            # 检查目标版本分支是否存在，存在则返回该仓库信息
            branch = f"openEuler-{os_version}"
            if branch in branches:
                log.info(f"仓库 {repo_name}（{repo_url}）已找到目标版本分支 {branch}")
                yield repo_name, repo_url

    def get_openEuler_everything_pkgs(
            self, os_version: str, os_arch: str
    ) -> Generator[str, None, None]:
        """
        从 openEuler everything 源页面迭代        以迭代方式返回指定版本、架构的所有 RPM 包完整名称。

        Args:
            os_version: openEuler 版本号（如 "24.03-LTS-SP2"）
            os_arch: 系统架构（如 "x86_64", "aarch64"）

        Yields:
            str: RPM 包完整名称（如 "zvbi-devel-0.2.44-1.oe2403sp2.x86_64.rpm"）

        Raises:
            RuntimeError: 网络请求失败（如超时、404、500 等）
            ValueError: 页面解析失败（未找到任何 .rpm 包）
        """
        base_url_template = "https://dl-cdn.openeuler.openatom.cn/openEuler-{os_version}/everything/{os_arch}/Packages/"
        timeout = 15
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        target_url = base_url_template.format(os_version=os_version, os_arch=os_arch)

        try:
            with requests.Session() as session:
                session.mount('https://', requests.adapters.HTTPAdapter(
                    pool_connections=10,
                    pool_maxsize=10,
                    max_retries=3
                ))
                response = session.get(
                    url=target_url,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                html_content = response.text

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"获取页面失败！URL: {target_url}, 错误: {str(e)}") from e

        soup = BeautifulSoup(html_content, "html.parser")
        # 精确匹配.rpm链接，排除父目录和空链接
        pkg_links = soup.find_all(
            "a",
            href=lambda href: isinstance(href, str) and href.endswith(".rpm") and not href.startswith('../')
        )

        if not pkg_links:
            raise ValueError(f"页面解析失败！URL: {target_url}, 未找到任何 .rpm 包")

        for link in pkg_links:
            full_pkg_name = link.get("href", "").strip()
            if full_pkg_name:  # 过滤空字符串
                yield full_pkg_name



if __name__ == "__main__":
    # 初始化获取器
    oe = OpenEuler()
    for rpm in oe.get_openEuler_rpm_names_from_repo("24.03-LTS-SP2", "python-minio","https://gitee.com/src-openeuler/python-minio.git"):
        print(f"src_name:python-minio,rpm:{rpm}")
    # log.info("正在初始化 Gitee 模块...")
    # repos_generator = oe.get_openEuler_repo_names_and_urls(
    #     os_version="24.03-LTS-SP2"
    # )
    # log.info("正在获取 openEuler 24.03-LTS-SP2 x86_64 架构的仓库信息...")
    # count=0
    # for repo_name, repo_url in repos_generator:
    #     log.info(f"正在处理仓库: {repo_name}，地址: {repo_url}")
    #     count+=1
    #     print(f"{repo_name}：{repo_url}")
    # log.info("共获取到 %d 个仓库" % count)
    # 示例：获取 openEuler 24.03-LTS-SP2 x86_64 架构的所有包（迭代打印前 10 个）
    # pkg_generator = oe.get_openEuler_everything_pkgs(
    #     os_version="24.03-LTS-SP1",
    #     os_arch="x86_64"
    # )
    # count=0
    # for name in pkg_generator:
    #     count+=1
    #     print(f"{name}")
    # print("共获取到 %d 个软件包" % count)
    pass

